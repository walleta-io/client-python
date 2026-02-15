from typing import Callable

from ..utils import _discover


INSTALLERS = []


def register(f: Callable) -> Callable:
    INSTALLERS.append(f)
    return f


def install():
    for installer in INSTALLERS:
        installer()


_discover(__name__)
