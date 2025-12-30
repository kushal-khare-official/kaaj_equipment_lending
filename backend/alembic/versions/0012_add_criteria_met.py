"""Add criteria_met field to applications

Revision ID: 0012
Revises: 0011
Create Date: 2025-12-30

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0012_add_criteria_met'
down_revision = '0011_add_assigned_lender_program'
branch_labels = None
depends_on = None


def upgrade():
    # Add criteria_met field to applications table
    # This stores the count of criteria met by the best matching lender program
    op.add_column('applications', sa.Column('criteria_met', sa.Integer(), nullable=True))
    op.add_column('applications', sa.Column('criteria_total', sa.Integer(), nullable=True))


def downgrade():
    op.drop_column('applications', 'criteria_total')
    op.drop_column('applications', 'criteria_met')

