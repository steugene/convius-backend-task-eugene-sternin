"""Add is_active field to restaurants for soft delete

Revision ID: 2d8201e94556
Revises: 810b3300f3e1
Create Date: 2025-06-09 11:58:48.212309

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2d8201e94556'
down_revision = '810b3300f3e1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add column as nullable first
    op.add_column('restaurant', sa.Column('is_active', sa.Boolean(), nullable=True))

    # Update existing data - set all existing restaurants as active
    op.execute("UPDATE restaurant SET is_active = true WHERE is_active IS NULL")

    # Now make the column NOT NULL
    op.alter_column('restaurant', 'is_active', nullable=False)


def downgrade() -> None:
    op.drop_column('restaurant', 'is_active')
