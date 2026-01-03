from backend.settings import settings
print("DATABASE_URL:", settings.DATABASE_URL)
from backend.database.session import engine
print("ENGINE URL:", engine.url)

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from backend.database.session import SessionLocal
from backend.database.queries import crud
from backend.models import Vote, Category


def main():
    db: Session = SessionLocal()

    try:
        # Create Category
        category = crud.create_category(db, name="Test Category")
        print(f"Created category: id={category.id}, name={category.name}")

        # Create Vote and link Category
        vote = crud.create_vote(
            db=db,
            question="Test Vote",
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            category_ids=[category.id],
            is_active=True,
        )
        print(f"Created vote: id={vote.id}, question={vote.question}")

        # Create Donation
        donation, totals = register_coin_and_selection(
            db=db,
            vote_id=vote.id,
            category_id=category.id,
            amount_cents=100,  # 1 €
        )

        print(f"Donation created: id={donation.id}, amount={donation.amount}")
        print("Totals after donation:")
        print(totals)

    finally:
        db.close()


def register_coin_and_selection(
    db: Session,
    vote_id: int,
    category_id: int,
    amount_cents: int,
):
    donation = crud.create_donation(
        db=db,
        vote_id=vote_id,
        category_id=category_id,
        amount_cents=amount_cents,
    )
    totals = crud.totals_for_vote(db, vote_id=vote_id)
    return donation, totals


if __name__ == "__main__":
    main()
