"""
Vote Repository - Handles all database operations for Vote entities.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Iterable

from sqlalchemy import select, insert, delete
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .base_repository import BaseRepository
from backend.models import Vote
from backend.models.associations import vote_category


class VoteRepository(BaseRepository[Vote]):
    """Repository for Vote entity operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(db, Vote)

    async def create(
        self,
        question: str,
        start_time: datetime,
        end_time: datetime,
        category_ids: Iterable[int],
    ) -> Vote:
        """
        Create a new vote.

        Categories are associated in the order they appear in category_ids.
        The position in the list determines the display order.

        Args:
            question: Vote question text
            start_time: Vote start time
            end_time: Vote end time
            category_ids: List of category IDs to associate (order matters)

        Returns:
            Created Vote entity

        Raises:
            ValueError: If start_time is not before end_time
        """
        # Validate that start_time is before end_time
        if start_time >= end_time:
            raise ValueError(
                f"start_time ({start_time}) must be before end_time ({end_time})"
            )

        vote = Vote(
            question=question,
            start_time=start_time,
            end_time=end_time,
        )

        self.db.add(vote)
        await self.flush()  # Flush to get vote.id

        # Insert vote-category associations with position
        category_id_list = list(category_ids)
        for position, category_id in enumerate(category_id_list):
            stmt = insert(vote_category).values(
                vote_id=vote.id,
                category_id=category_id,
                position=position,
            )
            await self.db.execute(stmt)

        await self.commit()
        await self.refresh(vote)
        return vote

    async def get_by_id(self, vote_id: int) -> Optional[Vote]:
        """
        Get a vote by ID with categories eagerly loaded.

        Args:
            vote_id: Vote ID

        Returns:
            Vote entity with categories loaded, or None if not found
        """
        stmt = select(Vote).where(Vote.id == vote_id).options(selectinload(Vote.categories))
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def update(
        self,
        vote_id: int,
        question: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        category_ids: Optional[Iterable[int]] = None,
    ) -> Vote:
        """
        Update an existing vote.

        Args:
            vote_id: Vote ID
            question: Optional new question text
            start_time: Optional new start time
            end_time: Optional new end time
            category_ids: Optional new category IDs (replaces existing)

        Returns:
            Updated Vote entity

        Raises:
            NoResultFound: If vote doesn't exist
            ValueError: If start_time is not before end_time
        """
        vote = await self.get_by_id(vote_id)
        if not vote:
            raise NoResultFound(f"Vote id={vote_id} not found")

        if question is not None:
            vote.question = question
        if start_time is not None:
            vote.start_time = start_time
        if end_time is not None:
            vote.end_time = end_time
        if category_ids is not None:
            # Delete old associations
            delete_stmt = delete(vote_category).where(vote_category.c.vote_id == vote_id)
            await self.db.execute(delete_stmt)

            # Insert new associations with position
            category_id_list = list(category_ids)
            for position, category_id in enumerate(category_id_list):
                insert_stmt = insert(vote_category).values(
                    vote_id=vote_id,
                    category_id=category_id,
                    position=position,
                )
                await self.db.execute(insert_stmt)

        # Validate that start_time is before end_time
        if vote.start_time >= vote.end_time:
            raise ValueError(
                f"start_time ({vote.start_time}) must be before end_time ({vote.end_time})"
            )

        await self.flush()
        await self.refresh(vote)
        return vote

    async def get_active_by_time(self) -> Optional[Vote]:
        """
        Get the currently active vote based on timestamps.

        A vote is active if current time is between start_time and end_time.

        Returns:
            Active Vote or None if no vote is currently active
        """
        now = datetime.now(timezone.utc)

        stmt = (
            select(Vote)
            .where(Vote.start_time <= now)
            .where(Vote.end_time >= now)
            .order_by(Vote.id.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

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


