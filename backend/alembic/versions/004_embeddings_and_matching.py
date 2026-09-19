"""004_embeddings_and_matching

Revision ID: 004_embeddings_and_matching
Revises: 003_evidence
Create Date: 2026-09-19 14:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision: str = '004_embeddings_and_matching'
down_revision: Union[str, None] = '003_evidence'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add embedding column to jobs table
    op.add_column(
        'jobs',
        sa.Column('embedding', Vector(1536).with_variant(sa.JSON(), 'sqlite'), nullable=True)
    )
    # Add embedding column to resumes table
    op.add_column(
        'resumes',
        sa.Column('embedding', Vector(1536).with_variant(sa.JSON(), 'sqlite'), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('resumes', 'embedding')
    op.drop_column('jobs', 'embedding')
