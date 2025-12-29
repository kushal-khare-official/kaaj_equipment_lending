"""add interest rate fields to lender_programs

Revision ID: 0005_add_interest_rate_to_lender_program
Revises: 0004_add_term_to_lender_program
Create Date: 2025-12-29

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0005_add_interest_rate_to_lender_program'
down_revision = '0004_add_term_to_lender_program'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('lender_programs', sa.Column('interest_rate_min', sa.Numeric(5, 2), nullable=True))
    op.add_column('lender_programs', sa.Column('interest_rate_max', sa.Numeric(5, 2), nullable=True))
    op.add_column('lender_programs', sa.Column('interest_rate_default', sa.Numeric(5, 2), nullable=True))


def downgrade() -> None:
    op.drop_column('lender_programs', 'interest_rate_default')
    op.drop_column('lender_programs', 'interest_rate_max')
    op.drop_column('lender_programs', 'interest_rate_min')
