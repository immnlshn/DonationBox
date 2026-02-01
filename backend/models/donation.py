from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

# Note: No imports of Vote or Category to avoid circular imports
# Use string-based forward references in relationships instead

class Donation(Base):
    __tablename__ = "donations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    vote_id: Mapped[int] = mapped_column(ForeignKey("votes.id", ondelete="CASCADE"), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False)

    # amount in cents
    amount: Mapped[int] = mapped_column(Integer, nullable=False)

    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # relationships (using string-based forward references)
    vote: Mapped["Vote"] = relationship(back_populates="donations")
    category: Mapped["Category"] = relationship(back_populates="donations")
 