import typing as ty

import aioredis
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine

from app.settings import settings


def create_start_app_handler(app: FastAPI) -> ty.Callable:
    async def start_app() -> None:
        app.state.db_pool = create_async_engine(
            settings.db_url.replace("postgresql://", "postgresql+asyncpg://"),
            pool_size=5,
        )
        app.state.cache = aioredis.Redis.from_url(settings.redis_url)

    return start_app


def create_stop_app_handler(app: FastAPI) -> ty.Callable:
    async def stop_app() -> None:
        await app.state.db_pool.dispose()
        await app.state.cache.close()

    return stop_app
