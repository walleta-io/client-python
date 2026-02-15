from typing import Self, Any, Type, Optional
from types import TracebackType

from walleta.compat import ContextVar
from walleta.models import UsageEventContext
from walleta.transport import send_usage, asend_usage
from walleta.interceptors import install


_current: ContextVar = ContextVar('walleta_context', default=None)


class context:
    def __init__(self, **kwargs: dict[str, Any]) -> None:
        self.data: dict[str, Any] = kwargs
        self.token: Any = None
        self.events: list[UsageEventContext] = []

    def add_event(self, event: UsageEventContext) -> None:
        event.add_context(self.data)
        self.events.append(event)

    def __enter__(self) -> Self:
        install()
        self.token = _current.set(self)
        return self

    def __exit__(self, exc_type: type[BaseException], exc_val: BaseException, exc_tb: TracebackType) -> None:
        _current.reset(self.token)
        usage_events = [
            e.to_usage_event() for e in self.usage_events
        ]
        send_usage(usage_events)
        self.events.clear()

    async def __aenter__(self) -> Self:
        return self.__enter__()

    async def __aexit__(self, exc_type: Type[Exception], exc_val: Exception, exc_tb: TracebackType) -> None:
        _current.reset(self.token)
        usage_events = [
            e.to_usage_event() for e in self.events
        ]
        await asend_usage(usage_events)
        self.events.clear()


def _get_current_context() -> Optional[context]:
    return _current.get()
