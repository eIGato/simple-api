import asyncio
import inspect

import asyncpg
from asyncpg import exceptions
from sqlalchemy.engine.url import (
    URL,
    make_url,
)


async def pg_connect(*args, init=None, **kwargs):
    conn = await asyncpg.connect(*args, **kwargs)
    if init is not None:
        try:
            await init(conn)
        except (Exception, asyncio.CancelledError) as exc:
            try:
                await conn.close()
            finally:
                raise exc
    return conn


_orig_sig = inspect.signature(asyncpg.connect)
pg_connect.__signature__ = _orig_sig.replace(  # type: ignore
    parameters=[
        *_orig_sig.parameters.values(),
        inspect.Parameter(
            "init", inspect.Parameter.KEYWORD_ONLY, default=None
        ),
    ]
)


async def connect(**db_settings):
    dsn = db_settings.get("dsn")
    make_url(dsn)
    connect_args = inspect.getcallargs(pg_connect)  # type: ignore
    # db_settings may have pool parameters which are not applicable here
    params = {
        arg: value
        for (arg, value) in {**db_settings}.items()
        if arg in connect_args
    }
    return await pg_connect(**params)


CREATE_DROP_EXCEPTIONS = (
    exceptions.InvalidCatalogNameError,
    exceptions.DuplicateDatabaseError,
)


async def _connect_system_db(db_params):
    url = make_url(db_params["dsn"])
    new_url = URL.create(
        drivername=url.drivername,
        username=url.username,
        password=url.password,
        host=url.host,
        database="postgres",
        query=url.query,
    )
    system_db_params = dict(
        db_params,
        dsn=str(new_url),
    )
    return await connect(**system_db_params)


def db_name_from_settings(db_params):
    return make_url(db_params["dsn"]).database


async def drop_db(db_params):
    conn = await _connect_system_db(db_params)
    db_name = db_name_from_settings(db_params)
    try:
        await conn.execute(f"DROP DATABASE IF EXISTS {db_name}")
    finally:
        await conn.close()


async def create_db(db_params, delete_existing=False, report=lambda m: None):
    db_name = db_name_from_settings(db_params)
    conn = await _connect_system_db(db_params)
    try:
        if delete_existing:
            try:
                await conn.execute(f"DROP DATABASE  {db_name}")
            except CREATE_DROP_EXCEPTIONS:
                pass

        try:
            await conn.execute(f"CREATE DATABASE  {db_name}")
        except CREATE_DROP_EXCEPTIONS:
            return False
    finally:
        await conn.close()
    return True
