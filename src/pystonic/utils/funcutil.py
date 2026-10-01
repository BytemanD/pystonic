import time
from collections.abc import Callable
from functools import wraps

from loguru import logger


def timeit(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start_time
        logger.info(f"{func.__name__} took {elapsed:.4f} seconds")
        return result

    return wrapper
