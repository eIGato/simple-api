import asyncio
import logging

import databases
import pytest
from sqlalchemy import create_engine

from app.core.database import metadata
from app.settings import settings

from . import setup

DB_URL = settings.db_url + "_test"
python_range = range
logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def setup_test_database():
    asyncio.run(setup.create_db({"dsn": DB_URL}))
    try:
        yield
    finally:
        asyncio.run(setup.drop_db({"dsn": DB_URL}))


@pytest.fixture(scope="session")
def test_database(setup_test_database):
    database = databases.Database(DB_URL)
    return database


@pytest.fixture(scope="session")
def test_engine(setup_test_database):
    engine = create_engine(DB_URL)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture(autouse=True)
async def connect_db(test_engine, test_database):
    metadata.create_all(bind=test_engine)
    try:
        async with test_database:
            yield test_database
    finally:
        logger.info("Dropping all data in DB")
        metadata.drop_all(bind=test_engine)
