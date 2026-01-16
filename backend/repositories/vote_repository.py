"""
Vote Repository - Handles all database operations for Vote entities.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional, Iterable

from sqlalchemy import select, update
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from .base_repository import BaseRepository
from backend.models import Vote, Category


class VoteRepository(BaseRepository[Vote]):
    """Repository for Vote entity operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(db, Vote)

    async def create(
        self,
        question: str,
        start_time: datetime,
        end_time: datetime,
        category_ids: Optional[Iterable[int]] = None,
        is_active: bool = False,
    ) -> Vote:
        """
        Create a new vote.

        Args:
            question: Vote question text
            start_time: Vote start time
            end_time: Vote end time
            category_ids: Optional list of category IDs to associate
            is_active: Whether vote should be active

        Returns:
            Created Vote entity
        """
        vote = Vote(
            question=question,
            start_time=start_time,
            end_time=end_time,
            is_active=is_active,
        )

        if category_ids:
            result = await self.db.execute(
                select(Category).where(Category.id.in_(list(category_ids)))
            )
            categories = list(result.scalars().all())
            vote.categories = categories

        self.db.add(vote)
        await self.commit()
        await self.refresh(vote)
        return vote

    async def get_active(self) -> Optional[Vote]:
        """
        Get the currently active vote.

        Returns:
            Active Vote or None if no vote is active
        """
        stmt = select(Vote).where(Vote.is_active.is_(True)).order_by(Vote.id.desc())
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def set_active(self, vote_id: int) -> None:
        """
        Set a vote as active and deactivate all others.

        Args:
            vote_id: ID of vote to activate

        Raises:
            NoResultFound: If vote with given ID doesn't exist
        """
        await self.db.execute(update(Vote).values(is_active=False))
        res = await self.db.execute(
            update(Vote).where(Vote.id == vote_id).values(is_active=True)
        )
        if res.rowcount == 0:
            await self.rollback()
            raise NoResultFound(f"Vote id={vote_id} not found")
        await self.commit()

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[Vote]:
        """
        List all votes with pagination.

        Args:
            limit: Maximum number of votes to return
            offset: Number of votes to skip

        Returns:
            List of Vote entities
        """
        stmt = select(Vote).order_by(Vote.id.desc()).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, vote_id: int) -> bool:
        """
        Delete a vote. Cascades to donations.

        Args:
            vote_id: ID of vote to delete

        Returns:
            True if deleted, False if not found
        """
        vote = await self.get_by_id(vote_id)
        if not vote:
            return False
        await self.db.delete(vote)
        await self.commit()
        return True

    async def add_categories(self, vote_id: int, category_ids: Iterable[int]) -> Vote:
        """
        Add categories to a vote.

        Args:
            vote_id: Vote ID
            category_ids: Category IDs to add

        Returns:
            Updated Vote entity

        Raises:
            NoResultFound: If vote doesn't exist
        """
        vote = await self.get_by_id(vote_id)
        if not vote:
            raise NoResultFound(f"Vote id={vote_id} not found")

        result = await self.db.execute(
            select(Category).where(Category.id.in_(list(category_ids)))
        )
        categories = list(result.scalars().all())

        existing_ids = {c.id for c in vote.categories}
        for c in categories:
            if c.id not in existing_ids:
                vote.categories.append(c)

        await self.commit()
        await self.refresh(vote)
        return vote

    async def remove_categories(self, vote_id: int, category_ids: Iterable[int]) -> Vote:
        """
        Remove categories from a vote.

        Args:
            vote_id: Vote ID
            category_ids: Category IDs to remove

        Returns:
            Updated Vote entity

        Raises:
            NoResultFound: If vote doesn't exist
        """
        vote = await self.get_by_id(vote_id)
        if not vote:
            raise NoResultFound(f"Vote id={vote_id} not found")

        remove_set = set(category_ids)
        vote.categories = [c for c in vote.categories if c.id not in remove_set]

        await self.commit()
        await self.refresh(vote)
        return vote

