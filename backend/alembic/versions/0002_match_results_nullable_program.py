"""make lender_program_id nullable in match_results

Revision ID: 0002_match_results_nullable_program
Revises: 0001_initial
Create Date: 2025-12-29
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_match_results_nullable_program"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    # SQLite doesn't support ALTER COLUMN, use batch mode to recreate table
    # Note: SQLite batch mode will recreate table with new schema
    with op.batch_alter_table("match_results", schema=None) as batch_op:
        batch_op.alter_column(
            "lender_program_id",
            existing_type=sa.Uuid(),
            nullable=True,
        )


def downgrade():
    with op.batch_alter_table("match_results", schema=None) as batch_op:
        batch_op.alter_column(
            "lender_program_id",
            existing_type=sa.Uuid(),
            nullable=False,
        )
