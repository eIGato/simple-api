from datetime import datetime  # noqa

import sqlalchemy as sa

from app.core.database import (
    Base,
    utc_now,
)

__all__ = ("User",)


class User(Base):
    __tablename__ = "user"

    id: int = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    name: str = sa.Column(sa.String(length=15), nullable=False, unique=True)
    email: str = sa.Column(sa.String(length=127), nullable=False, unique=True)
    password_hash: str = sa.Column(sa.String(length=64), nullable=False)
    created_at: datetime = sa.Column(
        sa.DateTime,
        nullable=False,
        default=utc_now,
    )
    updated_at: datetime = sa.Column(
        sa.DateTime,
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )
