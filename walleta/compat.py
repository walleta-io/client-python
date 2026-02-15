import warnings
import threading

# ContextVar fallback for Python < 3.7
try:
    from contextvars import ContextVar
except ImportError:

    class ContextVar:
        def __init__(self, name, default=None):
            self.name = name
            self._thread_local = threading.local()
            self._default = default

        def set(self, value):
            old = getattr(self._thread_local, self.name, self._default)
            setattr(self._thread_local, self.name, value)
            return old

        def get(self):
            return getattr(self._thread_local, self.name, self._default)

        def reset(self, value):
            setattr(self._thread_local, self.name, value)  # fixed typo

    warnings.warn(
        "Walleta context collection may not work properly in async code in Python < 3.7"
    )


# Async send implementation depending on installed library
async def _no_asend(url, payload):
    warnings.warn("No async client, install httpx or aiohttp")


try:
    import httpx

    async def _asend(url, payload):
        async with httpx.AsyncClient() as client:
            await client.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )

except ImportError:
    _asend = _no_asend


try:
    import aiohttp

    _prev_asend = _asend  # keep httpx if present

    async def _asend(url, payload):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as resp:
                await resp.text()

except ImportError:
    pass  # keep existing _asend
