import logging
import random
from hashlib import sha256

import aioredis
import pydantic
import sqlalchemy as sa
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
)
from sqlalchemy.ext.asyncio import AsyncConnection
from starlette import status
from starlette.requests import Request

from app import models

logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth")
auth_router = APIRouter()


class Token(pydantic.BaseModel):
    access_token: str
    token_type: str


@auth_router.post("/auth", response_model=Token)
async def authenticate(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    logger.debug(f"Got request: {form_data}")
    db: AsyncConnection = request.state.db
    users = await db.execute(
        sa.select(models.User).where(
            (models.User.name == form_data.username)
            & (
                models.User.password_hash
                == sha256((form_data.password).encode()).hexdigest()
            )
            & (models.User.deleted_at == None)
        )
    )
    if not users:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    [user] = users
    return Token(
        access_token=await create_access_token(
            user_id=user["id"],
            cache=request.app.state.cache,
        ),
        token_type="bearer",
    )


async def create_access_token(user_id, *, cache: aioredis.Redis):
    key = random.randbytes(4).hex()
    await cache.set(f"token_{key}", user_id)
    return key
