import base64
import logging
import typing as ty
from datetime import datetime
from hashlib import sha256

import pydantic as pydantic
import sqlalchemy as sa
from cryptography.fernet import Fernet
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncConnection
from starlette import status
from starlette.responses import Response

from app import models
from app.core.database import utc_now

from .auth import oauth2_scheme

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
    # TODO: Check if name and email fit in 32 chars. And other checks.
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
async def read_user(request: Request, id: int):
    db: AsyncConnection = request.state.db
    users = await db.execute(
        sa.select(models.User).where(
            (models.User.id == id) & (models.User.deleted_at == None)
        )
    )
    if not users:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    [user] = users
    return User(**user)


@users_router.patch("/{id}", response_model=User)
async def update_user(
    request: Request,
    id: int,
    user_info: UserUpdateInfo,
    token: str = Depends(oauth2_scheme),
):
    logger.debug(f"Got request: {user_info}")
    logger.debug(f"Got token: {token}")
    user_id = int(await request.app.state.cache.get(f"token_{token}"))
    logger.debug(f"Got user_id: {user_id}")
    if user_id != id:
        raise HTTPException(status.HTTP_403_FORBIDDEN)
    db = request.state.db
    to_update = {
        key: getattr(user_info, key)
        for key in ["name", "email"]
        if getattr(user_info, key)
    }
    if user_info.password:
        to_update["password_hash"] = sha256(
            user_info.password.encode()
        ).hexdigest()
    [user] = await db.execute(
        sa.update(models.User)
        .where(models.User.id == int(id))
        .values(**to_update)
        .returning(*models.User.__table__.c)
    )
    return User(**user)


@users_router.delete(
    "/{id}",
    response_class=Response,
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user(
    request: Request,
    id: int,
    token: str = Depends(oauth2_scheme),
):
    user_id = int(await request.app.state.cache.get(f"token_{token}"))
    if user_id != id:
        raise HTTPException(status.HTTP_403_FORBIDDEN)
    db = request.state.db
    users = await db.execute(
        sa.select(models.User)
        .with_for_update()
        .where((models.User.id == id) & (models.User.deleted_at == None))
    )
    if not users:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    [user] = users
    password_hash = user["password_hash"]
    fernet = Fernet(key=base64.b64encode(bytes.fromhex(password_hash)))
    # Unreadable data are still recoverable with password.
    # TODO: Add a recovery endpoint.
    await db.execute(
        sa.update(models.User)
        .where(models.User.id == id)
        .values(
            deleted_at=utc_now(),
            name=fernet.encrypt(user["name"].encode()).hex(),
            email=fernet.encrypt(user["email"].encode()).hex(),
            password_hash="",
        )
    )


@users_router.get("/", response_model=list[UserInList])
async def list_users(
    request: Request,
    limit: int = DEFAULT_LIMIT,
    offset: int = 0,
):
    db: AsyncConnection = request.state.db
    users = await db.execute(
        sa.select(models.User)
        .where(models.User.deleted_at == None)
        .limit(limit if limit > 0 else DEFAULT_LIMIT)
        .offset(max(offset, 0))
    )
    return [UserInList(**user) for user in users]
