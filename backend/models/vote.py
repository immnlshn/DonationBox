from __future__ import annotations

from datetime import datetime
from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .associations import vote_category

# Note: No imports of Category or Donation to avoid circular imports
# Use string-based forward references in relationships instead

class Vote(Base):
    __tablename__ = "votes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question: Mapped[str] = mapped_column(String, nullable=False)

    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # relationships (using string-based forward references)
    categories: Mapped[list["Category"]] = relationship(
        secondary=vote_category,
        back_populates="votes",
        lazy="selectin",
        order_by=vote_category.c.position,
    )

    donations: Mapped[list["Donation"]] = relationship(
        back_populates="vote",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
