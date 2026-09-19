"""002_jobs_and_candidates
Revision ID: 002_jobs_and_candidates
Revises: 001_initial_auth_schema
Create Date: 2026-09-19 11:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002_jobs_and_candidates'
down_revision: Union[str, None] = '001_initial_auth_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Jobs table
    op.create_table(
        'jobs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('org_id', sa.String(length=36), nullable=False),
        sa.Column('created_by_user_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('department', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='draft'),
        sa.Column('raw_description', sa.Text(), nullable=False),
        sa.Column('optimized_description', sa.Text(), nullable=True),
        sa.Column('parsed_criteria', sa.JSON(), nullable=False),
        sa.Column('bias_risk_score', sa.Float(), nullable=True),
        sa.Column('bias_findings', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_jobs_id'), 'jobs', ['id'], unique=False)
    op.create_index(op.f('ix_jobs_org_id'), 'jobs', ['org_id'], unique=False)
    op.create_index(op.f('ix_jobs_created_by_user_id'), 'jobs', ['created_by_user_id'], unique=False)
    op.create_index(op.f('ix_jobs_title'), 'jobs', ['title'], unique=False)
    op.create_index(op.f('ix_jobs_department'), 'jobs', ['department'], unique=False)
    op.create_index(op.f('ix_jobs_status'), 'jobs', ['status'], unique=False)
    op.create_index(op.f('ix_jobs_created_at'), 'jobs', ['created_at'], unique=False)

    # 2. Job requirements table
    op.create_table(
        'job_requirements',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('job_id', sa.String(length=36), nullable=False),
        sa.Column('requirement_text', sa.Text(), nullable=False),
        sa.Column('requirement_type', sa.String(length=50), nullable=False, server_default='must_have'),
        sa.Column('category', sa.String(length=50), nullable=False, server_default='skill'),
        sa.Column('weight', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_job_requirements_id'), 'job_requirements', ['id'], unique=False)
    op.create_index(op.f('ix_job_requirements_job_id'), 'job_requirements', ['job_id'], unique=False)
    op.create_index(op.f('ix_job_requirements_requirement_type'), 'job_requirements', ['requirement_type'], unique=False)

    # 3. Candidates table
    op.create_table(
        'candidates',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('org_id', sa.String(length=36), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('location', sa.String(length=150), nullable=True),
        sa.Column('current_title', sa.String(length=150), nullable=True),
        sa.Column('current_company', sa.String(length=150), nullable=True),
        sa.Column('years_of_experience', sa.Float(), nullable=True),
        sa.Column('linkedin_url', sa.Text(), nullable=True),
        sa.Column('github_url', sa.Text(), nullable=True),
        sa.Column('portfolio_url', sa.Text(), nullable=True),
        sa.Column('parsed_profile', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_candidates_id'), 'candidates', ['id'], unique=False)
    op.create_index(op.f('ix_candidates_org_id'), 'candidates', ['org_id'], unique=False)
    op.create_index(op.f('ix_candidates_full_name'), 'candidates', ['full_name'], unique=False)
    op.create_index(op.f('ix_candidates_email'), 'candidates', ['email'], unique=False)
    op.create_index(op.f('ix_candidates_created_at'), 'candidates', ['created_at'], unique=False)
    op.create_index(op.f('ix_candidates_years_of_experience'), 'candidates', ['years_of_experience'], unique=False)

    # 4. Candidate skills table
    op.create_table(
        'candidate_skills',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('candidate_id', sa.String(length=36), nullable=False),
        sa.Column('skill_name', sa.String(length=100), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False, server_default='technical'),
        sa.Column('years_experience', sa.Float(), nullable=True),
        sa.Column('proficiency_level', sa.String(length=50), nullable=True),
        sa.Column('verification_status', sa.String(length=50), nullable=False, server_default='unverified'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_candidate_skills_id'), 'candidate_skills', ['id'], unique=False)
    op.create_index(op.f('ix_candidate_skills_candidate_id'), 'candidate_skills', ['candidate_id'], unique=False)
    op.create_index(op.f('ix_candidate_skills_skill_name'), 'candidate_skills', ['skill_name'], unique=False)
    op.create_index(op.f('ix_candidate_skills_verification_status'), 'candidate_skills', ['verification_status'], unique=False)

    # 5. Resumes table
    op.create_table(
        'resumes',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('candidate_id', sa.String(length=36), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.Text(), nullable=False),
        sa.Column('file_type', sa.String(length=50), nullable=False),
        sa.Column('file_size_bytes', sa.Integer(), nullable=False),
        sa.Column('raw_text', sa.Text(), nullable=False),
        sa.Column('parsing_status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('parsing_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_resumes_id'), 'resumes', ['id'], unique=False)
    op.create_index(op.f('ix_resumes_candidate_id'), 'resumes', ['candidate_id'], unique=False)
    op.create_index(op.f('ix_resumes_parsing_status'), 'resumes', ['parsing_status'], unique=False)

    # 6. Candidate matches table
    op.create_table(
        'candidate_matches',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('job_id', sa.String(length=36), nullable=False),
        sa.Column('candidate_id', sa.String(length=36), nullable=False),
        sa.Column('overall_match_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('vector_similarity', sa.Float(), nullable=True),
        sa.Column('skill_overlap_score', sa.Float(), nullable=True),
        sa.Column('experience_fit_score', sa.Float(), nullable=True),
        sa.Column('reasoning', sa.Text(), nullable=False),
        sa.Column('matched_skills', sa.JSON(), nullable=False),
        sa.Column('missing_skills', sa.JSON(), nullable=False),
        sa.Column('pipeline_stage', sa.String(length=50), nullable=False, server_default='matched'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_candidate_matches_id'), 'candidate_matches', ['id'], unique=False)
    op.create_index(op.f('ix_candidate_matches_job_id'), 'candidate_matches', ['job_id'], unique=False)
    op.create_index(op.f('ix_candidate_matches_candidate_id'), 'candidate_matches', ['candidate_id'], unique=False)
    op.create_index(op.f('ix_candidate_matches_overall_match_score'), 'candidate_matches', ['overall_match_score'], unique=False)
    op.create_index(op.f('ix_candidate_matches_pipeline_stage'), 'candidate_matches', ['pipeline_stage'], unique=False)
    op.create_index(op.f('ix_candidate_matches_created_at'), 'candidate_matches', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_table('candidate_matches')
    op.drop_table('resumes')
    op.drop_table('candidate_skills')
    op.drop_table('candidates')
    op.drop_table('job_requirements')
    op.drop_table('jobs')
