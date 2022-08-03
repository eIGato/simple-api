import logging
import os

from pydantic import (
    BaseSettings,
    Field,
)

logging.basicConfig(level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")))


class Settings(BaseSettings):
    # TODO: graylog logging

    db_url: str = Field(..., env="DATABASE_URL")
    debug: bool = True
    project_name: str = "Simple API"
    redis_url: str = Field(..., env="REDIS_URL")


settings = Settings()
