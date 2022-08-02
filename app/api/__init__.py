from fastapi import APIRouter

from .users import users_router

api_router = APIRouter(prefix="/api")
api_router.include_router(users_router)
