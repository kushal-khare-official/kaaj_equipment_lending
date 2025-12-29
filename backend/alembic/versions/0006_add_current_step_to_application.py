"""add current_step to applications

Revision ID: 0006_add_current_step_to_application
Revises: 0005_add_interest_rate_to_lender_program
Create Date: 2025-12-29

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0006_add_current_step_to_application'
down_revision = '0005_add_interest_rate_to_lender_program'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('applications', sa.Column('current_step', sa.Integer(), nullable=True, server_default='1'))


def downgrade() -> None:
    op.drop_column('applications', 'current_step')
