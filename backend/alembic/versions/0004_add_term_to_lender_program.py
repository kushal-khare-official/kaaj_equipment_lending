"""add term fields to lender_programs

Revision ID: 0004_add_term_to_lender_program
Revises: 0003_add_business_name_loan_type
Create Date: 2025-12-29

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0004_add_term_to_lender_program'
down_revision = '0003_add_business_name_loan_type'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('lender_programs', sa.Column('term_min', sa.Integer(), nullable=True))
    op.add_column('lender_programs', sa.Column('term_max', sa.Integer(), nullable=True))
    op.add_column('lender_programs', sa.Column('term_default', sa.Integer(), nullable=True))
    op.add_column('lender_programs', sa.Column('term_used_equipment', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('lender_programs', 'term_used_equipment')
    op.drop_column('lender_programs', 'term_default')
    op.drop_column('lender_programs', 'term_max')
    op.drop_column('lender_programs', 'term_min')
