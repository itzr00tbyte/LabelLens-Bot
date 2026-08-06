"""add_spatial_scan_data_to_submissions

Revision ID: 591ee6108b69
Revises: None
Create Date: 2026-08-06 19:30:41.027900+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '591ee6108b69'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Idempotent: only add the column if it doesn't already exist.
    # This handles the case where init_db() previously ran create_all()
    # and the column was created before Alembic took over.
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_columns = [col["name"] for col in inspector.get_columns("submissions")]
    if "spatial_scan_data" not in existing_columns:
        op.add_column("submissions", sa.Column("spatial_scan_data", sa.JSON(), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_columns = [col["name"] for col in inspector.get_columns("submissions")]
    if "spatial_scan_data" in existing_columns:
        op.drop_column("submissions", "spatial_scan_data")
