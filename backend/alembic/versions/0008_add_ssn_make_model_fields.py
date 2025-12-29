"""add ssn to guarantors and make/model to equipment

Revision ID: 0008_add_ssn_make_model_fields
Revises: 0007_add_workflow_state_fields
Create Date: 2025-12-29

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0008_add_ssn_make_model_fields'
down_revision = '0007_add_workflow_state_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('guarantors', sa.Column('ssn', sa.String(), nullable=True))
    op.add_column('equipment', sa.Column('make', sa.String(), nullable=True))
    op.add_column('equipment', sa.Column('model', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('equipment', 'model')
    op.drop_column('equipment', 'make')
    op.drop_column('guarantors', 'ssn')
