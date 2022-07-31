from datetime import (
    datetime,
    timezone,
)

from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base

metadata = MetaData()
Base = declarative_base(metadata=metadata)


def utc_now():
    dt = datetime.now(timezone.utc)
    return dt.replace(tzinfo=None)


def utc_today():
    return utc_now().date()
