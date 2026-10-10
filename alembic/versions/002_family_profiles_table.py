"""create_family_profiles_table

Revision ID: 002_family_profiles_table
Revises: 001_initial_schema
Create Date: 2026-10-11 00:30:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002_family_profiles_table'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'family_profiles',
        sa.Column('profile_id', sa.String(36), nullable=False),
        sa.Column('owner_user_id', sa.String(36), nullable=False),
        sa.Column('member_name', sa.String(100), nullable=False),
        sa.Column('relation', sa.String(20), nullable=False),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('gender', sa.String(20), nullable=True),
        sa.Column('abha_id', sa.String(20), nullable=True),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.PrimaryKeyConstraint('profile_id'),
    )
    op.create_index('ix_family_profiles_owner_user_id', 'family_profiles', ['owner_user_id'])
    op.create_index('ix_family_profiles_is_primary', 'family_profiles', ['is_primary'])


def downgrade() -> None:
    op.drop_index('ix_family_profiles_is_primary', table_name='family_profiles')
    op.drop_index('ix_family_profiles_owner_user_id', table_name='family_profiles')
    op.drop_table('family_profiles')
