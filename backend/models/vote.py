from __future__ import annotations

from typing import TYPE_CHECKING
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Integer, String, Table, Column, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
if TYPE_CHECKING:
    from .category import Category
    from .donation import Donation

# Association table (M:N)
vote_category = Table(
    "vote_category",
    Base.metadata,
    Column("vote_id", ForeignKey("votes.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True),
)

class Vote(Base):
    __tablename__ = "votes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question: Mapped[str] = mapped_column(String, nullable=False)

    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # relationships
    categories: Mapped[list["Category"]] = relationship(
        secondary=vote_category,
        back_populates="votes",
        lazy="selectin",
    )

    donations: Mapped[list["Donation"]] = relationship(
        back_populates="vote",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
