from functools import wraps
from typing import Any, Callable
import asyncio

from .loop import create_event_loop


def async_to_sync_method(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(self, *args, **kwargs) -> Any:
        # 检查是否已经在事件循环中运行
        try:
            running_loop = asyncio.get_running_loop()
            # 如果已经在事件循环中，尝试使用 nest_asyncio
            try:
                import nest_asyncio
                nest_asyncio.apply()
                return running_loop.run_until_complete(func(self, *args, **kwargs))
            except ImportError:
                # 如果没有 nest_asyncio，抛出更明确的错误
                raise RuntimeError(
                    "Cannot run async function in existing event loop. "
                    "Please install nest_asyncio or call this function from outside an event loop."
                )
        except RuntimeError:
            # 没有运行中的事件循环，使用原来的逻辑
            loop = create_event_loop()
            return loop.run_until_complete(func(self, *args, **kwargs))

    return wrapper
