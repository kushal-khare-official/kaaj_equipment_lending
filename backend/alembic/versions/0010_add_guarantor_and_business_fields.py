"""add guarantor and business fields

Revision ID: 0010_add_guarantor_and_business_fields
Revises: 0009_add_review_status_fields
Create Date: 2025-12-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0010_add_guarantor_and_business_fields'
down_revision: Union[str, None] = '0009_add_review_status_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add business fields to applications table
    op.add_column('applications', sa.Column('business_tin', sa.String(), nullable=True))
    op.add_column('applications', sa.Column('business_phone', sa.String(), nullable=True))
    op.add_column('applications', sa.Column('business_address_street', sa.String(), nullable=True))
    op.add_column('applications', sa.Column('business_address_city', sa.String(), nullable=True))
    op.add_column('applications', sa.Column('business_address_state', sa.String(), nullable=True))
    op.add_column('applications', sa.Column('business_address_zip', sa.String(), nullable=True))
    op.add_column('applications', sa.Column('incorporation_date', sa.Date(), nullable=True))

    # Add guarantor fields
    op.add_column('guarantors', sa.Column('dob', sa.Date(), nullable=True))
    op.add_column('guarantors', sa.Column('phone', sa.String(), nullable=True))
    op.add_column('guarantors', sa.Column('email', sa.String(), nullable=True))
    op.add_column('guarantors', sa.Column('address_street', sa.String(), nullable=True))
    op.add_column('guarantors', sa.Column('address_city', sa.String(), nullable=True))
    op.add_column('guarantors', sa.Column('address_state', sa.String(), nullable=True))
    op.add_column('guarantors', sa.Column('address_zip', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove guarantor fields
    op.drop_column('guarantors', 'address_zip')
    op.drop_column('guarantors', 'address_state')
    op.drop_column('guarantors', 'address_city')
    op.drop_column('guarantors', 'address_street')
    op.drop_column('guarantors', 'email')
    op.drop_column('guarantors', 'phone')
    op.drop_column('guarantors', 'dob')

    # Remove business fields
    op.drop_column('applications', 'incorporation_date')
    op.drop_column('applications', 'business_address_zip')
    op.drop_column('applications', 'business_address_state')
    op.drop_column('applications', 'business_address_city')
    op.drop_column('applications', 'business_address_street')
    op.drop_column('applications', 'business_phone')
    op.drop_column('applications', 'business_tin')
