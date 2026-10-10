"""add_profile_id_to_existing_tables

Revision ID: 003_add_profile_id
Revises: 002_family_profiles_table
Create Date: 2026-10-11 00:30:01
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

revision: str = '003_add_profile_id'
down_revision: Union[str, None] = '002_family_profiles_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # IMPORTANT: Run this migration on a DB backup first.
    
    tables_to_update = ['health_records', 'risk_scores', 'reminders', 'doctor_reports']
    
    # 1. Add nullable profile_id to all 5 tables
    for table in tables_to_update + ['clinical_parameters']:
        op.add_column(table, sa.Column('profile_id', sa.String(length=36), nullable=True))

    # 2. Backfill profile_id for 4 tables
    for table in tables_to_update:
        op.execute(
            f"""
            UPDATE {table} 
            SET profile_id = (
                SELECT profile_id 
                FROM family_profiles 
                WHERE owner_user_id = {table}.user_id 
                AND is_primary = 1
            )
            """
        )

    # 3. Backfill for clinical_parameters via JOIN to health_records
    op.execute(
        """
        UPDATE clinical_parameters 
        SET profile_id = (
            SELECT profile_id 
            FROM health_records 
            WHERE health_records.record_id = clinical_parameters.record_id
        )
        """
    )

    # 4. Assertions
    for table in tables_to_update + ['clinical_parameters']:
        conn = op.get_bind()
        result = conn.execute(text(f"SELECT COUNT(*) FROM {table} WHERE profile_id IS NULL"))
        count = result.scalar()
        if count > 0:
            raise Exception(f"Backfill failed: NULL profile_ids remain in {table}")

    # 5 & 6 & 7. Alter to NOT NULL, add FKs, add indexes
    for table in tables_to_update + ['clinical_parameters']:
        # Note: SQLite alter_column with nullable=False can be tricky but assuming it works or we use batch
        with op.batch_alter_table(table) as batch_op:
            batch_op.alter_column('profile_id', nullable=False)
            batch_op.create_foreign_key(
                f'fk_{table}_profile_id',
                'family_profiles',
                ['profile_id'],
                ['profile_id'],
                ondelete='CASCADE'
            )
            batch_op.create_index(f'ix_{table}_profile_id', ['profile_id'])

    # 8. Add composite index on clinical_parameters
    with op.batch_alter_table('clinical_parameters') as batch_op:
        batch_op.create_index('ix_clinical_parameters_profile_date', ['profile_id', 'report_date'])


def downgrade() -> None:
    tables = ['health_records', 'risk_scores', 'reminders', 'doctor_reports', 'clinical_parameters']
    
    with op.batch_alter_table('clinical_parameters') as batch_op:
        batch_op.drop_index('ix_clinical_parameters_profile_date')

    for table in tables:
        with op.batch_alter_table(table) as batch_op:
            batch_op.drop_index(f'ix_{table}_profile_id')
            batch_op.drop_constraint(f'fk_{table}_profile_id', type_='foreignkey')
            batch_op.drop_column('profile_id')
