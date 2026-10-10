"""initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-10 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. health_records
    op.create_table(
        'health_records',
        sa.Column('record_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False, server_default='local_user'),
        sa.Column('record_type', sa.String(length=50), nullable=False),
        sa.Column('upload_date', sa.DateTime(), nullable=False),
        sa.Column('report_date', sa.DateTime(), nullable=False),
        sa.Column('source_file_path', sa.String(length=500), nullable=True),
        sa.Column('raw_text', sa.Text(), nullable=True),
        sa.Column('extracted_entities', sa.JSON(), nullable=True),
        sa.Column('encryption_hash', sa.String(length=128), nullable=True),
        sa.Column('is_processed', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('share_token', sa.Text(), nullable=True),
        sa.Column('share_expires_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('record_id')
    )
    op.create_index('ix_health_records_user_id', 'health_records', ['user_id'])
    op.create_index('ix_health_records_is_deleted', 'health_records', ['is_deleted'])

    # 2. clinical_parameters
    op.create_table(
        'clinical_parameters',
        sa.Column('param_id', sa.String(length=36), nullable=False),
        sa.Column('record_id', sa.String(length=36), nullable=False),
        sa.Column('param_name', sa.String(length=100), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(length=50), nullable=False),
        sa.Column('reference_range_min', sa.Float(), nullable=True),
        sa.Column('reference_range_max', sa.Float(), nullable=True),
        sa.Column('report_date', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='NORMAL'),
        sa.Column('anomaly_score', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['record_id'], ['health_records.record_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('param_id')
    )
    op.create_index('ix_clinical_parameters_record_id', 'clinical_parameters', ['record_id'])
    op.create_index('ix_clinical_parameters_param_name', 'clinical_parameters', ['param_name'])
    op.create_index('ix_clinical_parameters_report_date', 'clinical_parameters', ['report_date'])

    # 3. risk_scores
    op.create_table(
        'risk_scores',
        sa.Column('score_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('computed_at', sa.DateTime(), nullable=False),
        sa.Column('overall_risk', sa.Float(), nullable=False),
        sa.Column('risk_level', sa.String(length=20), nullable=False),
        sa.Column('contributing_factors', sa.JSON(), nullable=True),
        sa.Column('recommendations', sa.JSON(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.PrimaryKeyConstraint('score_id')
    )
    op.create_index('ix_risk_scores_user_id', 'risk_scores', ['user_id'])
    op.create_index('ix_risk_scores_computed_at', 'risk_scores', ['computed_at'])

    # 4. reminders
    op.create_table(
        'reminders',
        sa.Column('reminder_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False, server_default='local_user'),
        sa.Column('reminder_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('due_date', sa.DateTime(), nullable=False),
        sa.Column('recurrence', sa.String(length=50), nullable=False, server_default='NONE'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('is_acknowledged', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_from_record_id', sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(['created_from_record_id'], ['health_records.record_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('reminder_id')
    )
    op.create_index('ix_reminders_user_id', 'reminders', ['user_id'])
    op.create_index('ix_reminders_due_date', 'reminders', ['due_date'])
    op.create_index('ix_reminders_is_active', 'reminders', ['is_active'])
    op.create_index('ix_reminders_is_acknowledged', 'reminders', ['is_acknowledged'])

    # 5. doctor_reports
    op.create_table(
        'doctor_reports',
        sa.Column('report_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False, server_default='local_user'),
        sa.Column('generated_at', sa.DateTime(), nullable=False),
        sa.Column('report_content', sa.Text(), nullable=False),
        sa.Column('pdf_path', sa.String(length=500), nullable=True),
        sa.Column('records_included', sa.JSON(), nullable=True),
        sa.Column('share_token', sa.Text(), nullable=True),
        sa.Column('share_expires_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('report_id')
    )
    op.create_index('ix_doctor_reports_user_id', 'doctor_reports', ['user_id'])
    op.create_index('ix_doctor_reports_generated_at', 'doctor_reports', ['generated_at'])


def downgrade() -> None:
    op.drop_table('doctor_reports')
    op.drop_table('reminders')
    op.drop_table('risk_scores')
    op.drop_table('clinical_parameters')
    op.drop_table('health_records')
