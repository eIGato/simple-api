import typing as ty

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine

from app.settings import settings


def create_start_app_handler(app: FastAPI) -> ty.Callable:
    async def start_app() -> None:
        app.state.db_pool = create_async_engine(
            settings.db_url.replace("postgresql://", "postgresql+asyncpg://"),
            pool_size=5,
        )

    return start_app


def create_stop_app_handler(app: FastAPI) -> ty.Callable:
    async def stop_app() -> None:
        await app.state.db_pool.dispose()

    return stop_app
