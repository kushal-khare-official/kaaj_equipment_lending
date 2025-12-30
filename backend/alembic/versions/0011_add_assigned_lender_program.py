"""Add assigned lender program fields to applications

Revision ID: 0011
Revises: 0010
Create Date: 2025-12-30

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0011_add_assigned_lender_program'
down_revision = '0010_add_guarantor_and_business_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Add assigned lender program fields to applications table
    op.add_column('applications', sa.Column('assigned_lender_program_id', sa.Uuid(), nullable=True))
    op.add_column('applications', sa.Column('assigned_term_months', sa.Integer(), nullable=True))
    op.add_column('applications', sa.Column('assigned_interest_rate', sa.Numeric(5, 2), nullable=True))

    # Create foreign key constraint (if supported by database)
    # Note: SQLite doesn't support adding FK after table creation, so we make this conditional
    try:
        op.create_foreign_key(
            'fk_applications_assigned_lender_program',
            'applications', 'lender_programs',
            ['assigned_lender_program_id'], ['id'],
            ondelete='SET NULL'
        )
    except Exception:
        # SQLite doesn't support adding FK constraints after table creation
        pass


def downgrade():
    try:
        op.drop_constraint('fk_applications_assigned_lender_program', 'applications', type_='foreignkey')
    except Exception:
        pass
    op.drop_column('applications', 'assigned_interest_rate')
    op.drop_column('applications', 'assigned_term_months')
    op.drop_column('applications', 'assigned_lender_program_id')
