"""Add review status fields to application

Revision ID: 0009_add_review_status_fields
Revises: 0008_add_ssn_make_model_fields
Create Date: 2025-12-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0009_add_review_status_fields'
down_revision: Union[str, None] = '0008_add_ssn_make_model_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add review status fields to applications table
    op.add_column('applications', sa.Column('review_status', sa.String(), nullable=True))
    op.add_column('applications', sa.Column('requires_manual_review', sa.Boolean(), nullable=True))
    op.add_column('applications', sa.Column('reviewed_by', sa.String(), nullable=True))
    op.add_column('applications', sa.Column('reviewed_at', sa.DateTime(), nullable=True))

    # Set default review_status for existing applications
    op.execute("UPDATE applications SET review_status = 'pending' WHERE review_status IS NULL")
    op.execute("UPDATE applications SET requires_manual_review = false WHERE requires_manual_review IS NULL")


def downgrade() -> None:
    op.drop_column('applications', 'reviewed_at')
    op.drop_column('applications', 'reviewed_by')
    op.drop_column('applications', 'requires_manual_review')
    op.drop_column('applications', 'review_status')
