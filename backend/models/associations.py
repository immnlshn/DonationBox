"""
Association tables for many-to-many relationships.
These are defined separately to avoid circular imports.
"""
from sqlalchemy import Table, Column, ForeignKey

from .base import Base

# Association table for Vote <-> Category (M:N)
vote_category = Table(
    "vote_category",
    Base.metadata,
    Column("vote_id", ForeignKey("votes.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True),
)
