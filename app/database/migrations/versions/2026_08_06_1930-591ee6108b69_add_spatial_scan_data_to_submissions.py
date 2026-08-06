"""add_spatial_scan_data_to_submissions

Revision ID: 591ee6108b69
Revises: None
Create Date: 2026-08-06 19:30:41.027900+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '591ee6108b69'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add spatial_scan_data JSON column to submissions table.
    # NOTE: The alter_column for users.is_approved is intentionally omitted —
    # SQLite does not support ALTER COLUMN, and the column is already correct in the model.
    op.add_column('submissions', sa.Column('spatial_scan_data', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('submissions', 'spatial_scan_data')
