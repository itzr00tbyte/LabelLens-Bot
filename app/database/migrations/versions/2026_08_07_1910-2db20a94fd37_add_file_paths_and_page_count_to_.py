"""add_file_paths_and_page_count_to_submissions

Revision ID: 2db20a94fd37
Revises: '591ee6108b69'
Create Date: 2026-08-07 19:10:17.607048+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '2db20a94fd37'
down_revision: Union[str, None] = '591ee6108b69'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_columns = [col["name"] for col in inspector.get_columns("submissions")]

    with op.batch_alter_table('submissions', schema=None) as batch_op:
        if 'original_file_path' not in existing_columns:
            batch_op.add_column(sa.Column('original_file_path', sa.String(length=512), nullable=True))
        if 'processed_image_path' not in existing_columns:
            batch_op.add_column(sa.Column('processed_image_path', sa.String(length=512), nullable=True))
        if 'generated_png_path' not in existing_columns:
            batch_op.add_column(sa.Column('generated_png_path', sa.String(length=512), nullable=True))
        if 'generated_pdf_path' not in existing_columns:
            batch_op.add_column(sa.Column('generated_pdf_path', sa.String(length=512), nullable=True))
        if 'page_count' not in existing_columns:
            batch_op.add_column(sa.Column('page_count', sa.Integer(), server_default='1', nullable=False))
        if 'replacement_images' not in existing_columns:
            batch_op.add_column(sa.Column('replacement_images', sa.JSON(), server_default='{}', nullable=False))
        if 'template_version' not in existing_columns:
            batch_op.add_column(sa.Column('template_version', sa.Integer(), server_default='1', nullable=False))


def downgrade() -> None:
    with op.batch_alter_table('submissions', schema=None) as batch_op:
        batch_op.drop_column('template_version')
        batch_op.drop_column('replacement_images')
        batch_op.drop_column('page_count')
        batch_op.drop_column('generated_pdf_path')
        batch_op.drop_column('generated_png_path')
        batch_op.drop_column('processed_image_path')
        batch_op.drop_column('original_file_path')
