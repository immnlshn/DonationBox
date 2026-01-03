from __future__ import annotations

from typing import TYPE_CHECKING
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .vote import vote_category  # association table
if TYPE_CHECKING:
    from .vote import Vote
    from .donation import Donation

class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    votes: Mapped[list["Vote"]] = relationship(
        secondary=vote_category,
        back_populates="categories",
        lazy="selectin",
    )

    donations: Mapped[list["Donation"]] = relationship(
        back_populates="category",
        lazy="selectin",
    )
