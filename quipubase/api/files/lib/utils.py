from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from functools import partial, reduce, wraps
from typing import Awaitable, Callable, Coroutine, Type, TypeVar, Union, cast
from uuid import uuid4

import base64c as base64  # type: ignore
from cachetools import TTLCache, cached
from typing_extensions import ParamSpec

T = TypeVar("T")
P = ParamSpec("P")


@dataclass
class QuipubaseException(BaseException):
    detail: str
    status_code: int = field(default=500)


def get_key(*, object: dict[str, T], key: str) -> T | None:
    try:
        return object[key]
    except KeyError:
        return None


def chunker(seq: str, size: int = 1000):
    return (seq[pos : pos + size] for pos in range(0, len(seq), size))


def ttl_cache(
    maxsize: int = 128, ttl: int = 3600 * 24 * 365
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        """
        A decorator that wraps a function with caching functionality.

        This decorator uses a TTL (Time-To-Live) cache to store the results of the
        function calls. The cache is defined with a maximum size and a TTL value,
        which determines how long the results are stored in the cache.

        Args:
            func (Callable[P, T]): The function to be decorated.

        Returns:
            Callable[P, T]: The wrapped function with caching applied.
        """

        @wraps(func)
        @cached(cache=TTLCache[str, T](maxsize, ttl))
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            return func(*args, **kwargs)

        return wrapper

    return decorator


def b64_id() -> str:
    """
    Generates a URL-safe base64 encoded string from a UUID4.

    Returns:
        str: A URL-safe base64 encoded string representation of a UUID4, with padding removed.
    """
    return base64.urlsafe_b64encode(uuid4().bytes).decode("utf-8").rstrip("=")


def get_logger(
    name: str | None = None,
    level: int = logging.DEBUG,
    format_string: str = json.dumps(
        {
            "timestamp": "%(asctime)s",
            "level": "%(levelname)s",
            "name": "%(name)s",
            "message": "%(message)s",
        }
    ),
) -> logging.Logger:
    """
    Configures and returns a logger with a specified name, level, and format.

    :param name: Name of the logger. If None, the root logger will be configured.
    :param level: Logging level, e.g., logging.INFO, logging.DEBUG.
    :param format_string: Format string for log messages.
    :return: Configured logger.
    """
    if name is None:
        name = "AnyDocs"
        name = "🚀 {name} 🚀"
    logger_ = logging.getLogger(name)
    logger_.setLevel(level)
    if not logger_.handlers:
        ch = logging.StreamHandler()
        formatter = logging.Formatter(format_string)
        ch.setFormatter(formatter)
        logger_.addHandler(ch)
    return logging.getLogger(name)


logger = get_logger()


def exception_handler(
    func: Callable[P, T],
) -> Callable[P, Union[T, Coroutine[None, T, T]]]:
    """
    Decorator to handle exceptions in a function.

    :param func: Function to be decorated.
    :return: Decorated function.
    """

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error("%s: %s", e.__class__.__name__, e)
            raise QuipubaseException(
                status_code=500,
                detail=f"Internal Server Error: {e.__class__.__name__} => {e}",
            ) from e

    async def awrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        try:
            func_ = cast(Awaitable[T], func(*args, **kwargs))
            return await func_
        except Exception as e:
            logger.error("%s: %s", e.__class__.__name__, e)
            raise QuipubaseException(
                status_code=500,
                detail=f"Internal Server Error: {e.__class__.__name__} => {e}",
            ) from e

    if asyncio.iscoroutinefunction(func):
        awrapper.__name__ = func.__name__
        return awrapper
    wrapper.__name__ = func.__name__
    return wrapper


def timing_handler(
    func: Callable[P, T],
) -> Callable[P, Union[T, Coroutine[None, T, T]]]:
    """
    Decorator to measure the time taken by a function.

    :param func: Function to be decorated.
    :return: Decorated function.
    """

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        logger.info("%s took %s seconds", func.__name__, end - start)
        return result

    async def awrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        start = time.time()
        func_ = cast(Awaitable[T], func(*args, **kwargs))
        result = await func_
        end = time.time()
        logger.info("%s took %s seconds", func.__name__, end - start)
        return result

    if asyncio.iscoroutinefunction(func):
        awrapper.__name__ = func.__name__
        return awrapper
    wrapper.__name__ = func.__name__
    return wrapper


def retry_handler(
    func: Callable[P, T], retries: int = 3, delay: int = 1
) -> Callable[P, Union[T, Coroutine[None, T, T]]]:
    """
    Decorator to retry a function with exponential backoff.

    :param func: Function to be decorated.
    :param retries: Number of retries.
    :param delay: Delay between retries.
    :return: Decorated function.
    """

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        nonlocal delay
        for _ in range(retries):
            try:
                return func(*args, **kwargs)
            except QuipubaseException as e:
                logger.error("%s: %s", e.__class__.__name__, e)
                time.sleep(delay)
                delay *= 2
                continue
        raise QuipubaseException(
            status_code=500, detail=f"Exhausted retries after {retries} attempts"
        )

    @wraps(func)
    async def awrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        nonlocal delay
        for _ in range(retries):
            try:
                func_ = cast(Awaitable[T], func(*args, **kwargs))
                return await func_
            except QuipubaseException as e:
                logger.error("%s: %s", e.__class__.__name__, e)
                await asyncio.sleep(delay)
                delay *= 2
        raise QuipubaseException(
            status_code=500,
            detail="Exhausted retries",
        )

    if asyncio.iscoroutinefunction(func):
        awrapper.__name__ = func.__name__
        return awrapper
    wrapper.__name__ = func.__name__
    return wrapper


def handle(
    func: Callable[P, T], retries: int = 3, delay: int = 1
) -> Callable[P, Union[T, Coroutine[None, T, T]]]:
    """
    Decorator to retry a function with exponential backoff and handle exceptions.

    :param func: Function to be decorated.
    :param retries: Number of retries.
    :param delay: Delay between retries.
    :return: Decorated function.
    """
    eb = partial(retry_handler, retries=retries, delay=delay)
    return cast(
        Callable[P, Union[T, Coroutine[None, T, T]]],
        reduce(lambda f, g: g(f), [exception_handler, timing_handler, eb], func),  # type: ignore
    )


def asyncify(func: Callable[P, T]) -> Callable[P, Coroutine[None, T, T]]:
    """
    Decorator to convert a synchronous function to an asynchronous function.

    :param func: Synchronous function to be decorated.
    :return: Asynchronous function.
    """

    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        wrapper.__name__ = func.__name__
        return await asyncio.to_thread(func, *args, **kwargs)

    return wrapper


def singleton(cls: Type[T]) -> Type[T]:
    """
    Decorator that converts a class into a singleton.

    Args:
                    cls (Type[T]): The class to be converted into a singleton.

    Returns:
                    Type[T]: The singleton instance of the class.
    """
    instances: dict[Type[T], T] = {}

    @wraps(cls)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return cast(Type[T], wrapper)


def coalesce(*args: T) -> T | None:
    """
    Returns the first non-None argument.

    :param args: Arguments to be coalesced.
    :return: First non-None argument.
    """
    for arg in args:
        if arg is not None:
            return arg
    raise ValueError("No arguments provided")


def merge_dicts(*dicts: dict[str, T]) -> dict[str, T]:
    """
    Merges multiple dictionaries into one.
    """
    return {k: v for d in dicts for k, v in d.items()}


def _new_event_loop():
    loop = asyncio.get_event_loop()
    asyncio.set_event_loop(loop)
    return loop


def get_loop():
    try:
        loop = asyncio.get_running_loop()
        if loop.is_running():
            return loop
        else:
            loop.close()
        return _new_event_loop()
    except RuntimeError as e:
        logger.error("Event loop wasn't running %s", e)
        return _new_event_loop()
    except Exception as e:
        logger.error("Unexpected error %s", e)
        raise e
