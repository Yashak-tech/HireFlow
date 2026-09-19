"""003_evidence

Revision ID: 003_evidence
Revises: 002_jobs_and_candidates
Create Date: 2026-09-19 12:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '003_evidence'
down_revision: Union[str, None] = '002_jobs_and_candidates'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'evidence',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('candidate_id', sa.String(length=36), nullable=False),
        sa.Column('resume_id', sa.String(length=36), nullable=True),
        sa.Column('answer_id', sa.String(length=36), nullable=True),
        sa.Column('claim_type', sa.String(length=50), nullable=False),
        sa.Column('claim_text', sa.Text(), nullable=False),
        sa.Column('verbatim_source_text', sa.Text(), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=False, server_default='resume'),
        sa.Column('confidence_score', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('is_overridden_by_human', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('overridden_by_user_id', sa.String(length=36), nullable=True),
        sa.Column('override_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['overridden_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_evidence_id'), 'evidence', ['id'], unique=False)
    op.create_index(op.f('ix_evidence_candidate_id'), 'evidence', ['candidate_id'], unique=False)
    op.create_index(op.f('ix_evidence_resume_id'), 'evidence', ['resume_id'], unique=False)
    op.create_index(op.f('ix_evidence_answer_id'), 'evidence', ['answer_id'], unique=False)
    op.create_index(op.f('ix_evidence_claim_type'), 'evidence', ['claim_type'], unique=False)


def downgrade() -> None:
    op.drop_table('evidence')
