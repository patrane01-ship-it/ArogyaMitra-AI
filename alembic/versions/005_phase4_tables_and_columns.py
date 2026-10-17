"""phase4_tables_and_columns

Revision ID: 005_phase4_tables_and_columns
Revises: 004_phase3_new_tables
Create Date: 2026-10-17 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

revision: str = '005_phase4_tables_and_columns'
down_revision: Union[str, None] = '004_phase3_new_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. New Columns on Existing Tables ─────────────────────────────
    # clinical_parameters
    op.add_column('clinical_parameters', sa.Column('ref_source', sa.String(length=32), nullable=True, server_default='DEFAULT'))
    op.add_column('clinical_parameters', sa.Column('value_original', sa.Float(), nullable=True))
    op.add_column('clinical_parameters', sa.Column('unit_original', sa.String(length=50), nullable=True))
    op.add_column('clinical_parameters', sa.Column('value_normalized', sa.Float(), nullable=True))
    op.add_column('clinical_parameters', sa.Column('needs_review', sa.Boolean(), nullable=True, server_default=sa.text('0')))
    op.add_column('clinical_parameters', sa.Column('field_confidence', sa.Float(), nullable=True))

    # family_profiles
    op.add_column('family_profiles', sa.Column('sex', sa.String(length=20), nullable=True))
    op.add_column('family_profiles', sa.Column('is_minor', sa.Boolean(), nullable=False, server_default=sa.text('0')))

    # health_records
    op.add_column('health_records', sa.Column('file_hash', sa.String(length=64), nullable=True))
    op.add_column('health_records', sa.Column('stored_file_key', sa.String(length=255), nullable=True))
    op.create_index(op.f('ix_health_records_file_hash'), 'health_records', ['file_hash'])
    op.create_index(op.f('ix_health_records_stored_file_key'), 'health_records', ['stored_file_key'])

    # ── 2. New Phase 4 Tables ─────────────────────────────────────────
    # privacy_notice_versions
    op.create_table(
        'privacy_notice_versions',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('version', sa.String(length=32), nullable=False),
        sa.Column('language', sa.String(length=8), nullable=False, server_default='en'),
        sa.Column('notice_text', sa.Text(), nullable=False),
        sa.Column('text_hash', sa.String(length=64), nullable=False),
        sa.Column('effective_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_privacy_notice_versions_version'), 'privacy_notice_versions', ['version'], unique=True)

    # consent_records
    op.create_table(
        'consent_records',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('profile_id', sa.String(length=36), sa.ForeignKey('family_profiles.profile_id', ondelete='CASCADE'), nullable=True),
        sa.Column('purpose', sa.String(length=64), nullable=False),
        sa.Column('granted', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('notice_version', sa.String(length=32), nullable=False),
        sa.Column('method', sa.String(length=32), nullable=False, server_default='WEB_UI'),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_consent_records_user_id'), 'consent_records', ['user_id'])
    op.create_index(op.f('ix_consent_records_profile_id'), 'consent_records', ['profile_id'])
    op.create_index(op.f('ix_consent_records_purpose'), 'consent_records', ['purpose'])

    # guardian_consents
    op.create_table(
        'guardian_consents',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('profile_id', sa.String(length=36), sa.ForeignKey('family_profiles.profile_id', ondelete='CASCADE'), nullable=False),
        sa.Column('guardian_user_id', sa.String(length=36), sa.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('notice_version', sa.String(length=32), nullable=False),
        sa.Column('method', sa.String(length=64), nullable=False, server_default='SELF_ATTESTATION'),
        sa.Column('attested_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(op.f('ix_guardian_consents_profile_id'), 'guardian_consents', ['profile_id'], unique=True)
    op.create_index(op.f('ix_guardian_consents_guardian_user_id'), 'guardian_consents', ['guardian_user_id'])

    # data_export_jobs
    op.create_table(
        'data_export_jobs',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('profile_id', sa.String(length=36), sa.ForeignKey('family_profiles.profile_id', ondelete='CASCADE'), nullable=True),
        sa.Column('format', sa.String(length=32), nullable=False, server_default='JSON'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='PENDING'),
        sa.Column('file_key', sa.String(length=255), nullable=True),
        sa.Column('download_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_data_export_jobs_user_id'), 'data_export_jobs', ['user_id'])

    # erasure_requests
    op.create_table(
        'erasure_requests',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('scope', sa.String(length=32), nullable=False, server_default='PROFILE'),
        sa.Column('profile_id', sa.String(length=36), sa.ForeignKey('family_profiles.profile_id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='PENDING_GRACE'),
        sa.Column('grace_until', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(op.f('ix_erasure_requests_user_id'), 'erasure_requests', ['user_id'])

    # audit_log_entries
    op.create_table(
        'audit_log_entries',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('actor_type', sa.String(length=32), nullable=False),
        sa.Column('actor_id', sa.String(length=36), nullable=False),
        sa.Column('action', sa.String(length=64), nullable=False),
        sa.Column('target_type', sa.String(length=64), nullable=False),
        sa.Column('target_id', sa.String(length=64), nullable=True),
        sa.Column('profile_id', sa.String(length=36), nullable=True),
        sa.Column('request_id', sa.String(length=64), nullable=True),
        sa.Column('ip_hash', sa.String(length=64), nullable=True),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_audit_log_entries_actor_id'), 'audit_log_entries', ['actor_id'])
    op.create_index(op.f('ix_audit_log_entries_action'), 'audit_log_entries', ['action'])
    op.create_index(op.f('ix_audit_log_entries_occurred_at'), 'audit_log_entries', ['occurred_at'])

    # job_records
    op.create_table(
        'job_records',
        sa.Column('job_id', sa.String(length=36), primary_key=True),
        sa.Column('type', sa.String(length=64), nullable=False),
        sa.Column('owner_user_id', sa.String(length=36), sa.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('profile_id', sa.String(length=36), sa.ForeignKey('family_profiles.profile_id', ondelete='CASCADE'), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='QUEUED'),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_attempts', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('idempotency_key', sa.String(length=128), nullable=True),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.Column('last_error_code', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(op.f('ix_job_records_type'), 'job_records', ['type'])
    op.create_index(op.f('ix_job_records_owner_user_id'), 'job_records', ['owner_user_id'])
    op.create_index(op.f('ix_job_records_idempotency_key'), 'job_records', ['idempotency_key'], unique=True)

    # stored_file_keys
    op.create_table(
        'stored_file_keys',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('file_key', sa.String(length=255), nullable=False),
        sa.Column('wrapped_data_key', sa.Text(), nullable=False),
        sa.Column('nonce', sa.String(length=64), nullable=False),
        sa.Column('kek_version', sa.String(length=32), nullable=False),
        sa.Column('checksum', sa.String(length=64), nullable=False),
        sa.Column('size_bytes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_stored_file_keys_file_key'), 'stored_file_keys', ['file_key'], unique=True)
    op.create_index(op.f('ix_stored_file_keys_kek_version'), 'stored_file_keys', ['kek_version'])

    # ocr_corrections
    op.create_table(
        'ocr_corrections',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('param_id', sa.String(length=36), sa.ForeignKey('clinical_parameters.parameter_id', ondelete='CASCADE'), nullable=False),
        sa.Column('record_id', sa.String(length=36), sa.ForeignKey('health_records.record_id', ondelete='CASCADE'), nullable=False),
        sa.Column('original_value', sa.Float(), nullable=True),
        sa.Column('original_unit', sa.String(length=32), nullable=True),
        sa.Column('corrected_value', sa.Float(), nullable=False),
        sa.Column('corrected_unit', sa.String(length=32), nullable=False),
        sa.Column('field_confidence', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_ocr_corrections_param_id'), 'ocr_corrections', ['param_id'])

    # user_sessions
    op.create_table(
        'user_sessions',
        sa.Column('session_id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('refresh_family_id', sa.String(length=64), nullable=False),
        sa.Column('device_label', sa.String(length=255), nullable=True),
        sa.Column('ip_hash', sa.String(length=64), nullable=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_user_sessions_user_id'), 'user_sessions', ['user_id'])
    op.create_index(op.f('ix_user_sessions_refresh_family_id'), 'user_sessions', ['refresh_family_id'])


def downgrade() -> None:
    op.drop_table('user_sessions')
    op.drop_table('ocr_corrections')
    op.drop_table('stored_file_keys')
    op.drop_table('job_records')
    op.drop_table('audit_log_entries')
    op.drop_table('erasure_requests')
    op.drop_table('data_export_jobs')
    op.drop_table('guardian_consents')
    op.drop_table('consent_records')
    op.drop_table('privacy_notice_versions')

    op.drop_index(op.f('ix_health_records_stored_file_key'), table_name='health_records')
    op.drop_index(op.f('ix_health_records_file_hash'), table_name='health_records')
    op.drop_column('health_records', 'stored_file_key')
    op.drop_column('health_records', 'file_hash')

    op.drop_column('family_profiles', 'is_minor')
    op.drop_column('family_profiles', 'sex')

    op.drop_column('clinical_parameters', 'field_confidence')
    op.drop_column('clinical_parameters', 'needs_review')
    op.drop_column('clinical_parameters', 'value_normalized')
    op.drop_column('clinical_parameters', 'unit_original')
    op.drop_column('clinical_parameters', 'value_original')
    op.drop_column('clinical_parameters', 'ref_source')
