import functools
import json
import logging

from starlette.requests import Request

logger = logging.getLogger(__name__)


def make_cache_key(prefix: str, **kwargs):
    kwargs_serialized = "_".join([f"{k}_{v}" for k, v in kwargs.items()])
    return f"{prefix}_{kwargs_serialized}"


def cached(
    prefix: str | None = None,
    significant_args: list[str] | None = None,
):
    def decorate(coro):
        @functools.wraps(coro)
        async def wrapper(*args, request: Request, **kwargs):
            nonlocal prefix
            if prefix is None:
                prefix = coro.__name__
            nonlocal significant_args
            if significant_args is None:
                significant_args = sorted(kwargs.keys())
            cache = request.app.state.cache
            cache_key = make_cache_key(
                prefix=prefix,
                **{key: kwargs[key] for key in significant_args},
            )
            cached_result = await cache.get(cache_key)
            if cached_result:
                logger.debug(f"Found cached key {cache_key}")
                return json.loads(cached_result)

            result = await coro(*args, request=request, **kwargs)

            logger.debug(f"Caching key {cache_key}")
            await cache.set(cache_key, result.json())
            return result

        return wrapper

    if prefix is None or isinstance(prefix, str):
        return decorate
    else:
        return decorate(prefix)


def resets_cache(
    prefix: str,
    significant_args: list[str] | None = None,
):
    def decorate(coro):
        @functools.wraps(coro)
        async def wrapper(*args, request: Request, **kwargs):
            result = await coro(*args, request=request, **kwargs)

            nonlocal significant_args
            if significant_args is None:
                significant_args = sorted(kwargs.keys())
            cache = request.app.state.cache
            cache_key = make_cache_key(
                prefix=prefix,
                **{key: kwargs[key] for key in significant_args},
            )
            logger.debug(f"Resetting key {cache_key}")
            await cache.delete(cache_key)
            return result

        return wrapper

    return decorate
