import uvicorn
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request

from app.api import api_router
from app.core.events import (
    create_start_app_handler,
    create_stop_app_handler,
)
from app.settings import settings


async def db_session_middleware(request: Request, call_next):
    db_pool = request.app.state.db_pool
    async with db_pool.connect() as db:
        request.state.db = db
        response = await call_next(request)
        await db.commit()
    return response


def get_application() -> FastAPI:
    application = FastAPI(
        title=settings.project_name,
        debug=settings.debug,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_middleware(
        BaseHTTPMiddleware,
        dispatch=db_session_middleware,
    )
    application.add_event_handler(
        "startup", create_start_app_handler(application)
    )
    application.add_event_handler(
        "shutdown", create_stop_app_handler(application)
    )
    application.include_router(api_router)
    return application


app = get_application()

if __name__ == "__main__":
    uvicorn.run(
        "main:app", host="0.0.0.0", port=80, log_level="debug", reload=True
    )
