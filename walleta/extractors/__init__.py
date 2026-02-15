from abc import ABC
from abc import abstractmethod, abstractclassmethod
from typing import Callable, Optional

from walleta.models import HttpData, UsageEventContext
from walleta.utils import _discover


EXTRACTORS = []


class ResponseHandler(ABC):
    host: str = None

    def __init__(self, http_data: HttpData) -> None:
        self.http_data = http_data

    @abstractclassmethod
    def match(cls, http_data: HttpData) -> bool:
        return http_data.host == cls.host

    @abstractmethod
    def handle_chunk(self, chunk: bytes) -> None:
        raise NotImplementedError()

    @abstractmethod
    def finalize(self) -> Optional[UsageEventContext]:
        raise NotImplementedError()


def register(f: Callable) -> Callable:
    EXTRACTORS.append(f)
    return f


def search(http_data: HttpData) -> Optional[ResponseHandler]:
    for extractor_cls in EXTRACTORS:
        if extractor.match(http_data):
            return extractor_cls(http_data)


_discover(__name__)
