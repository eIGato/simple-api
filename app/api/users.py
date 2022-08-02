import logging
import typing as ty
from datetime import datetime
from hashlib import sha256

import pydantic as pydantic
import sqlalchemy as sa
from fastapi import (
    APIRouter,
    HTTPException,
    Request,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncConnection
from starlette import status
from starlette.responses import Response

from app import models

DEFAULT_LIMIT = 10
logger = logging.getLogger(__name__)
users_router = APIRouter(prefix="/users")


class User(pydantic.BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime
    updated_at: datetime


class UserCreateInfo(pydantic.BaseModel):
    name: str
    email: str
    password: str


class UserUpdateInfo(pydantic.BaseModel):
    name: ty.Optional[str]
    email: ty.Optional[str]
    password: ty.Optional[str]


class UserInList(pydantic.BaseModel):
    id: int
    name: str


@users_router.post(
    "/",
    response_model=User,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(request: Request, user_info: UserUpdateInfo):
    logger.debug(f"Got request: {user_info}")
    db = request.state.db
    try:
        [user] = await db.execute(
            sa.insert(models.User)
            .values(
                name=user_info.name,
                email=user_info.email,
                password_hash=sha256(user_info.password.encode()).hexdigest(),
            )
            .returning(*models.User.__table__.c)
        )
    except IntegrityError as e:
        raise HTTPException(400, "This name or email already exists") from e
    return User(**user)


@users_router.get("/{id}", response_model=User)
async def read_user(request: Request, id: str):
    db: AsyncConnection = request.state.db
    users = await db.execute(
        sa.select(models.User).where(models.User.id == int(id))
    )
    if not users:
        raise HTTPException(404)
    [user] = users
    return User(**user)


@users_router.patch("/{id}", response_model=User)
async def update_user(request: Request, id: str, user_info: UserUpdateInfo):
    logger.debug(f"Got request: {user_info}")
    db = request.state.db
    try:
        to_update = {
            key: getattr(user_info, key)
            for key in ["name", "email"]
            if getattr(user_info, key)
        }
        if user_info.password:
            to_update["password_hash"] = sha256(
                user_info["password"].encode()
            ).hexdigest()
        [user] = await db.execute(
            sa.update(models.User)
            .where(models.User.id == int(id))
            .values(**to_update)
            .returning(*models.User.__table__.c)
        )
    except Exception as e:
        raise HTTPException(400) from e
    return User(**user)


@users_router.delete(
    "/{id}",
    response_class=Response,
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user(request: Request, id: str):
    db = request.state.db
    try:
        await db.execute(
            sa.delete(models.User).where(models.User.id == int(id))
        )
    except Exception as e:
        raise HTTPException(400) from e


@users_router.get("/", response_model=list[User])
async def list_users(
    request: Request,
    limit: int = DEFAULT_LIMIT,
    offset: int = 0,
):
    db: AsyncConnection = request.state.db
    users = await db.execute(
        sa.select(models.User)
        .limit(limit if limit > 0 else DEFAULT_LIMIT)
        .offset(max(offset, 0))
    )
    return list(map(UserInList, users))