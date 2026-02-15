
import pkgutil
import importlib

from contextlib import contextmanager
from time import perf_counter


def _discover(package_name: str) -> None:
    for module_info in pkgutil.iter_modules(__path__):
        name = module_info.name

        if name.startswith('_') or name == 'registry':
            continue

        importlib.import_module(f'{package_name}.{name}')


@contextmanager
def timer():
    start = perf_counter()
    elapsed = object()
    try:
        yield elapsed

    finally:
        setattr(elapsed, 'seconds', perf_counter() - start)
