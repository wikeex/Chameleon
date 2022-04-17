import asyncio
import time
from functools import wraps

from log import logger


def delay(func, seconds: int = 30):
    """
    延迟函数，调用方法前先等待seconds秒
    :param func:
    :param seconds:
    :return:
    """
    if asyncio.iscoroutinefunction(func):
        @wraps(func)
        async def wrapper(self, *args, **kw):
            await asyncio.sleep(seconds)
            return await func(self, *args, **kw)
    else:
        @wraps(func)
        def wrapper(self, *args, **kw):
            time.sleep(seconds)
            return func(self, *args, **kw)

    return wrapper


def exception_catch(func):
    if asyncio.iscoroutinefunction(func):
        @wraps(func)
        async def wrapper(self, *args, **kw):
            try:
                return await func(self, *args, **kw)
            except Exception as e:
                logger.error(f'调用方法{func}时发生错误：{e}', exc_info=True)
    else:
        @wraps(func)
        def wrapper(self, *args, **kw):
            try:
                return func(self, *args, **kw)
            except Exception as e:
                logger.error(f'调用方法{func}时发生错误：{e}', exc_info=True)

    return wrapper
