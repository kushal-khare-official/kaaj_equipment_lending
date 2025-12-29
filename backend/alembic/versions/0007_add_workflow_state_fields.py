"""Add workflow state fields to application

Revision ID: 0007_add_workflow_state_fields
Revises: 0006_add_current_step_to_application
Create Date: 2025-12-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0007_add_workflow_state_fields'
down_revision: Union[str, None] = '0006_add_current_step_to_application'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add workflow state fields to applications table
    op.add_column('applications', sa.Column('workflow_step', sa.String(), nullable=True))
    op.add_column('applications', sa.Column('workflow_status', sa.String(), nullable=True))
    op.add_column('applications', sa.Column('risk_level', sa.String(), nullable=True))
    op.add_column('applications', sa.Column('risk_flags', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('applications', 'risk_flags')
    op.drop_column('applications', 'risk_level')
    op.drop_column('applications', 'workflow_status')
    op.drop_column('applications', 'workflow_step')
