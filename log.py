import inspect
import sys
import types
from functools import lru_cache

from loguru import logger

logger.remove()


@lru_cache(None)
def get_console(format):
    logger.add(
        sys.stdout,  # open('/dev/null', 'w'),
        level="INFO",
        filter=lambda rec: rec['extra']['format'] == format,
        format=format,
    )
    return logger.bind(format=format).info


def get_callable_representation(obj):
    if isinstance(obj, types.FunctionType) and obj.__name__ == '<lambda>':
        return inspect.getsource(obj).strip()
    return obj
