"""Add soft delete feature.

Revision ID: 79a91a05b3aa
Revises: 22287a40b4f7
Create Date: 2022-08-03 15:57:39.188172

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "79a91a05b3aa"
down_revision = "22287a40b4f7"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "user", sa.Column("deleted_at", sa.DateTime(), nullable=True)
    )


def downgrade():
    op.drop_column("user", "deleted_at")
