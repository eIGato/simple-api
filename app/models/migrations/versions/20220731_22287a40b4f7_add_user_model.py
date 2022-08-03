"""Add user model.

Revision ID: 22287a40b4f7
Revises:
Create Date: 2022-07-31 14:17:51.256950

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "22287a40b4f7"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("email", sa.String(length=64), nullable=False),
        sa.Column("password_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("name"),
    )


def downgrade():
    op.drop_table("user")
