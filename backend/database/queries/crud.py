from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, Optional

from sqlalchemy import Select, delete, func, select, update
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from backend.models import Category, Donation, Vote, vote_category


# ============================================================
# Helpers
# ============================================================

def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ============================================================
# CATEGORY CRUD
# ============================================================

def create_category(db: Session, name: str) -> Category:
    category = Category(name=name)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def get_category_by_id(db: Session, category_id: int) -> Optional[Category]:
    return db.get(Category, category_id)


def get_category_by_name(db: Session, name: str) -> Optional[Category]:
    stmt = select(Category).where(Category.name == name)
    return db.execute(stmt).scalars().first()


def list_categories(db: Session) -> list[Category]:
    stmt = select(Category).order_by(Category.id.asc())
    return list(db.execute(stmt).scalars().all())


def delete_category(db: Session, category_id: int) -> bool:
    """
    Deleting a category might fail if donations reference it and FK is RESTRICT.
    Return True if deleted, False if not found.
    """
    category = db.get(Category, category_id)
    if not category:
        return False
    db.delete(category)
    db.commit()
    return True


# ============================================================
# VOTE CRUD
# ============================================================

def create_vote(
    db: Session,
    question: str,
    start_time: datetime,
    end_time: datetime,
    category_ids: Iterable[int] | None = None,
    is_active: bool = False,
) -> Vote:
    vote = Vote(
        question=question,
        start_time=start_time,
        end_time=end_time,
        is_active=is_active,
    )

    if category_ids:
        categories = list(
            db.execute(select(Category).where(Category.id.in_(list(category_ids))))
            .scalars()
            .all()
        )
        vote.categories = categories

    db.add(vote)
    db.commit()
    db.refresh(vote)
    return vote


def get_vote_by_id(db: Session, vote_id: int) -> Optional[Vote]:
    return db.get(Vote, vote_id)


def get_active_vote(db: Session) -> Optional[Vote]:
    stmt = select(Vote).where(Vote.is_active.is_(True)).order_by(Vote.id.desc())
    return db.execute(stmt).scalars().first()


def set_active_vote(db: Session, vote_id: int) -> None:
    """
    Makes exactly one vote active:
    - set all votes inactive
    - set chosen vote active
    """
    db.execute(update(Vote).values(is_active=False))
    res = db.execute(update(Vote).where(Vote.id == vote_id).values(is_active=True))
    if res.rowcount == 0:
        db.rollback()
        raise NoResultFound(f"Vote id={vote_id} not found")
    db.commit()


def list_votes(db: Session, limit: int = 100, offset: int = 0) -> list[Vote]:
    stmt = select(Vote).order_by(Vote.id.desc()).limit(limit).offset(offset)
    return list(db.execute(stmt).scalars().all())


def delete_vote(db: Session, vote_id: int) -> bool:
    """
    Vote deletion cascades to donations (FK ondelete=CASCADE + relationship cascade).
    """
    vote = db.get(Vote, vote_id)
    if not vote:
        return False
    db.delete(vote)
    db.commit()
    return True


def add_categories_to_vote(db: Session, vote_id: int, category_ids: Iterable[int]) -> Vote:
    vote = db.get(Vote, vote_id)
    if not vote:
        raise NoResultFound(f"Vote id={vote_id} not found")

    categories = list(
        db.execute(select(Category).where(Category.id.in_(list(category_ids))))
        .scalars()
        .all()
    )

    # avoid duplicates
    existing_ids = {c.id for c in vote.categories}
    for c in categories:
        if c.id not in existing_ids:
            vote.categories.append(c)

    db.commit()
    db.refresh(vote)
    return vote


def remove_categories_from_vote(db: Session, vote_id: int, category_ids: Iterable[int]) -> Vote:
    vote = db.get(Vote, vote_id)
    if not vote:
        raise NoResultFound(f"Vote id={vote_id} not found")

    remove_set = set(category_ids)
    vote.categories = [c for c in vote.categories if c.id not in remove_set]

    db.commit()
    db.refresh(vote)
    return vote


# ============================================================
# DONATION CRUD
# ============================================================

def create_donation(
    db: Session,
    vote_id: int,
    category_id: int,
    amount_cents: int,
    timestamp: datetime | None = None,
) -> Donation:
    donation = Donation(
        vote_id=vote_id,
        category_id=category_id,
        amount=amount_cents,
        timestamp=timestamp or utcnow(),
    )
    db.add(donation)
    db.commit()
    db.refresh(donation)
    return donation


def get_donation_by_id(db: Session, donation_id: int) -> Optional[Donation]:
    return db.get(Donation, donation_id)


def list_donations_for_vote(db: Session, vote_id: int) -> list[Donation]:
    stmt = select(Donation).where(Donation.vote_id == vote_id).order_by(Donation.id.asc())
    return list(db.execute(stmt).scalars().all())


def totals_for_vote(db: Session, vote_id: int) -> dict:
    """
    Returns totals useful for UI:
      - total_amount_cents
      - by_category: list[{category_id, category_name, amount_cents, count}]
    """
    total_stmt = select(func.coalesce(func.sum(Donation.amount), 0)).where(Donation.vote_id == vote_id)
    total_amount = int(db.execute(total_stmt).scalar_one())

    by_cat_stmt = (
        select(
            Donation.category_id.label("category_id"),
            Category.name.label("category_name"),
            func.coalesce(func.sum(Donation.amount), 0).label("amount_cents"),
            func.count(Donation.id).label("count"),
        )
        .join(Category, Category.id == Donation.category_id)
        .where(Donation.vote_id == vote_id)
        .group_by(Donation.category_id, Category.name)
        .order_by(Donation.category_id.asc())
    )

    rows = db.execute(by_cat_stmt).all()
    by_category = [
        {
            "category_id": int(r.category_id),
            "category_name": str(r.category_name),
            "amount_cents": int(r.amount_cents),
            "count": int(r.count),
        }
        for r in rows
    ]

    return {"vote_id": vote_id, "total_amount_cents": total_amount, "by_category": by_category}


def totals_for_active_vote(db: Session) -> Optional[dict]:
    vote = get_active_vote(db)
    if not vote:
        return None
    return totals_for_vote(db, vote.id)


# ============================================================
# ADMIN / MAINTENANCE HELPERS (optional)
# ============================================================

def wipe_all_data(db: Session) -> None:
    """
    Dangerous: deletes everything. Useful for dev.
    Order matters due to FKs.
    """
    db.execute(delete(Donation))
    db.execute(delete(vote_category))
    db.execute(delete(Vote))
    db.execute(delete(Category))
    db.commit()
