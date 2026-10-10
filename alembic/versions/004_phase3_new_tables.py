"""phase3_new_tables

Revision ID: 004_phase3_new_tables
Revises: 003_add_profile_id
Create Date: 2026-10-11 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

revision: str = '004_phase3_new_tables'
down_revision: Union[str, None] = '003_add_profile_id'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. subscription_tiers
    op.create_table(
        'subscription_tiers',
        sa.Column('subscription_id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('tier', sa.String(length=20), nullable=False, server_default='FREE'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('payment_reference', sa.String(length=100), nullable=True),
        sa.Column('family_member_limit', sa.Integer(), nullable=False, server_default='2'),
        sa.Column('doctor_access_limit', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('prediction_enabled', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('wearable_enabled', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('api_access_enabled', sa.Boolean(), nullable=False, server_default=sa.text('0')),
    )
    op.create_index(op.f('ix_subscription_tiers_user_id'), 'subscription_tiers', ['user_id'], unique=True)

    # 2. prediction_results
    op.create_table(
        'prediction_results',
        sa.Column('prediction_id', sa.String(length=36), primary_key=True),
        sa.Column('profile_id', sa.String(length=36), nullable=False),
        sa.Column('param_name', sa.String(length=100), nullable=False),
        sa.Column('computed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('current_value', sa.Float(), nullable=False),
        sa.Column('current_trend', sa.String(length=20), nullable=False),
        sa.Column('slope', sa.Float(), nullable=False),
        sa.Column('months_to_threshold', sa.Integer(), nullable=True),
        sa.Column('threshold_value', sa.Float(), nullable=False),
        sa.Column('threshold_label', sa.String(length=200), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('data_points_used', sa.Integer(), nullable=False),
        sa.Column('alert_level', sa.String(length=20), nullable=False),
        sa.Column('narrative', sa.String(length=500), nullable=False)
    )
    op.create_index(op.f('ix_prediction_results_profile_id'), 'prediction_results', ['profile_id'])

    # 3. doctor_accesses
    op.create_table(
        'doctor_accesses',
        sa.Column('access_id', sa.String(length=36), primary_key=True),
        sa.Column('patient_profile_id', sa.String(length=36), nullable=False),
        sa.Column('granted_by_user_id', sa.String(length=36), nullable=False),
        sa.Column('doctor_name', sa.String(length=100), nullable=False),
        sa.Column('doctor_email', sa.String(length=255), nullable=False),
        sa.Column('doctor_registration_number', sa.String(length=50), nullable=True),
        sa.Column('specialization', sa.String(length=100), nullable=True),
        sa.Column('access_token', sa.String(length=36), nullable=False),
        sa.Column('granted_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('access_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('scope_json', sa.Text(), nullable=False)
    )
    op.create_index(op.f('ix_doctor_accesses_patient_profile_id'), 'doctor_accesses', ['patient_profile_id'])
    op.create_index(op.f('ix_doctor_accesses_access_token'), 'doctor_accesses', ['access_token'], unique=True)

    # 4. wearable_readings
    op.create_table(
        'wearable_readings',
        sa.Column('reading_id', sa.String(length=36), primary_key=True),
        sa.Column('profile_id', sa.String(length=36), nullable=False),
        sa.Column('source', sa.String(length=30), nullable=False),
        sa.Column('metric_type', sa.String(length=30), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(length=20), nullable=False),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('synced_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('raw_payload', sa.Text(), nullable=True),
        sa.Column('is_anomaly', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.UniqueConstraint('profile_id', 'source', 'metric_type', 'recorded_at', name='uq_wearable_dedup')
    )
    op.create_index(op.f('ix_wearable_readings_profile_id'), 'wearable_readings', ['profile_id'])

    # 5. whatsapp_sessions
    op.create_table(
        'whatsapp_sessions',
        sa.Column('session_id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('phone_number', sa.String(length=20), nullable=False),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('active_profile_id', sa.String(length=36), nullable=True),
        sa.Column('last_message_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('conversation_state', sa.Text(), nullable=True),
        sa.Column('otp_hash', sa.String(length=128), nullable=True),
        sa.Column('otp_expires_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index(op.f('ix_whatsapp_sessions_user_id'), 'whatsapp_sessions', ['user_id'])
    op.create_index(op.f('ix_whatsapp_sessions_phone_number'), 'whatsapp_sessions', ['phone_number'], unique=True)

    # 6. api_keys
    op.create_table(
        'api_keys',
        sa.Column('key_id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('api_key_hash', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('rate_limit', sa.Integer(), nullable=False, server_default='100')
    )
    op.create_index(op.f('ix_api_keys_user_id'), 'api_keys', ['user_id'])

    # 7. api_key_audit
    op.create_table(
        'api_key_audit',
        sa.Column('audit_id', sa.String(length=36), primary_key=True),
        sa.Column('key_id', sa.String(length=36), nullable=False),
        sa.Column('endpoint', sa.String(length=200), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('profile_id', sa.String(length=36), nullable=True)
    )
    op.create_index(op.f('ix_api_key_audit_key_id'), 'api_key_audit', ['key_id'])

    # 8. razorpay_events
    op.create_table(
        'razorpay_events',
        sa.Column('event_id', sa.String(length=100), primary_key=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=False)
    )

def downgrade() -> None:
    op.drop_table('razorpay_events')
    
    op.drop_index(op.f('ix_api_key_audit_key_id'), table_name='api_key_audit')
    op.drop_table('api_key_audit')
    
    op.drop_index(op.f('ix_api_keys_user_id'), table_name='api_keys')
    op.drop_table('api_keys')
    
    op.drop_index(op.f('ix_whatsapp_sessions_phone_number'), table_name='whatsapp_sessions')
    op.drop_index(op.f('ix_whatsapp_sessions_user_id'), table_name='whatsapp_sessions')
    op.drop_table('whatsapp_sessions')
    
    op.drop_index(op.f('ix_wearable_readings_profile_id'), table_name='wearable_readings')
    op.drop_table('wearable_readings')
    
    op.drop_index(op.f('ix_doctor_accesses_access_token'), table_name='doctor_accesses')
    op.drop_index(op.f('ix_doctor_accesses_patient_profile_id'), table_name='doctor_accesses')
    op.drop_table('doctor_accesses')
    
    op.drop_index(op.f('ix_prediction_results_profile_id'), table_name='prediction_results')
    op.drop_table('prediction_results')
    
    op.drop_index(op.f('ix_subscription_tiers_user_id'), table_name='subscription_tiers')
    op.drop_table('subscription_tiers')
