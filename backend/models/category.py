from __future__ import annotations

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .associations import vote_category

# Note: No imports of Vote or Donation to avoid circular imports
# Use string-based forward references in relationships instead

class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    # relationships (using string-based forward references)
    votes: Mapped[list["Vote"]] = relationship(
        secondary=vote_category,
        back_populates="categories",
        lazy="selectin",
    )

    donations: Mapped[list["Donation"]] = relationship(
        back_populates="category",
        lazy="selectin",
    )
