"""add business_name and loan_type to applications

Revision ID: 0003
Revises: 0002_match_results_nullable_program
Create Date: 2025-12-29

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0003_add_business_name_loan_type'
down_revision = '0002_match_results_nullable_program'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('applications', sa.Column('business_name', sa.String(), nullable=True))
    op.add_column('applications', sa.Column('loan_type', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('applications', 'loan_type')
    op.drop_column('applications', 'business_name')
