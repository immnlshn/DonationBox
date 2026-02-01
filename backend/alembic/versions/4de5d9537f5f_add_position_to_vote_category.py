"""add_position_to_vote_category

Revision ID: 4de5d9537f5f
Revises: 1fd9dd790eea
Create Date: 2026-02-01 17:12:08.296173

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4de5d9537f5f'
down_revision: Union[str, None] = '1fd9dd790eea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add position column to vote_category table
    op.add_column('vote_category', sa.Column('position', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    # Remove position column
    op.drop_column('vote_category', 'position')
