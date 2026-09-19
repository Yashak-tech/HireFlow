"""005_interviews_schema

Revision ID: 005_interviews_schema
Revises: 004_embeddings_and_matching
Create Date: 2026-09-19 15:00:00.000000

Phase 5: Interview Intelligence Agent — Creates interviews, interview_questions,
interview_answers, and evaluations tables.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '005_interviews_schema'
down_revision: Union[str, None] = '004_embeddings_and_matching'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Interviews table
    op.create_table(
        'interviews',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('job_id', sa.String(36), sa.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('candidate_id', sa.String(36), sa.ForeignKey('candidates.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('match_id', sa.String(36), sa.ForeignKey('candidate_matches.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('created_by_user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('status', sa.String(50), nullable=False, default='scheduled', index=True),
        sa.Column('current_question_index', sa.Integer, nullable=False, default=0),
        sa.Column('tamper_flag', sa.Boolean, nullable=False, default=False, index=True),
        sa.Column('tamper_details', sa.JSON, nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # 2. Interview Questions table
    op.create_table(
        'interview_questions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('interview_id', sa.String(36), sa.ForeignKey('interviews.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('order_index', sa.Integer, nullable=False, index=True),
        sa.Column('category', sa.String(50), nullable=False, index=True),
        sa.Column('question_text', sa.Text, nullable=False),
        sa.Column('intent', sa.Text, nullable=False),
        sa.Column('targeted_gap', sa.Text, nullable=True),
        sa.Column('rubric_criteria', sa.JSON, nullable=False, server_default='{}'),
        sa.Column('is_customized', sa.Boolean, nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # 3. Interview Answers table
    op.create_table(
        'interview_answers',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('question_id', sa.String(36), sa.ForeignKey('interview_questions.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('interview_id', sa.String(36), sa.ForeignKey('interviews.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('transcript_text', sa.Text, nullable=False),
        sa.Column('attempt_number', sa.Integer, nullable=False, default=1),
        sa.Column('follow_up_prompt', sa.Text, nullable=True),
        sa.Column('audio_recording_url', sa.Text, nullable=True),
        sa.Column('duration_seconds', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # 4. Evaluations table
    op.create_table(
        'evaluations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('interview_id', sa.String(36), sa.ForeignKey('interviews.id', ondelete='CASCADE'), nullable=False, unique=True, index=True),
        sa.Column('match_id', sa.String(36), sa.ForeignKey('candidate_matches.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('technical_score', sa.Float, nullable=False, default=0.0),
        sa.Column('communication_score', sa.Float, nullable=False, default=0.0),
        sa.Column('depth_score', sa.Float, nullable=False, default=0.0),
        sa.Column('overall_interview_score', sa.Float, nullable=False, default=0.0, index=True),
        sa.Column('category_scores', sa.JSON, nullable=False, server_default='{}'),
        sa.Column('strengths', sa.JSON, nullable=False, server_default='[]'),
        sa.Column('weaknesses', sa.JSON, nullable=False, server_default='[]'),
        sa.Column('executive_summary', sa.Text, nullable=False),
        sa.Column('ai_recommendation', sa.String(50), nullable=False, default='review_needed', index=True),
        sa.Column('human_decision', sa.String(50), nullable=True, index=True),
        sa.Column('human_decision_notes', sa.Text, nullable=True),
        sa.Column('human_decision_by_user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('human_decision_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )


def downgrade() -> None:
    op.drop_table('evaluations')
    op.drop_table('interview_answers')
    op.drop_table('interview_questions')
    op.drop_table('interviews')
