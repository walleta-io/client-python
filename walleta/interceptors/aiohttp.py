import logging
import time
import aiohttp

from walleta import extractors
from walleta.interceptors import register
from walleta.models import HttpData
from walleta.context import _get_current_context

LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())

try:
    _orig_request = aiohttp.ClientSession._request

except ImportError:
    aiohttp = None
    _orig_request = None


async def _patch_response_read(handler, response, ctx):
    orig_read = response.content.read

    async def read(n=-1):
        chunk = await orig_read(n)
        if chunk:
            handler.handle_chunk(chunk)
        else:
            event = handler.finalize()
            if event:
                ctx.add_usage(event)
        return chunk

    response.content.read = read


async def _patch_response_aclose(handler, response, ctx):
    orig_aclose = response.aclose

    async def aclose(*args, **kwargs):
        if not getattr(handler, "_finalized", False):
            if getattr(response.content, "_body", None) is None:
                await response.content.read()
            event = handler.finalize()
            if event:
                ctx.add_usage(event)
        return await orig_aclose(*args, **kwargs)

    response.aclose = aclose


async def _patched_request(self, method, url, *args, **kwargs):
    ctx = _get_current_context()
    with timer() as t:
        response = await _orig_request(self, method, url, *args, **kwargs)

    if not ctx:
        return response

    http_data = HttpData(
        host=response.url.host,
        method=method,
        url=str(response.url),
        request_headers=dict(kwargs.get("headers") or {}),
        request_body=kwargs.get("data"),
        response_status=response.status,
        response_headers=dict(response.headers),
        response_body=None,
        duration=t.seconds,
    )

    handler = extractors.search(http_data)
    if not handler:
        return response

    await _patch_response_read(handler, response, ctx)
    await _patch_response_aclose(handler, response, ctx)
    return response


@register
def install_aiohttp():
    if aiohttp is None:
        return

    if aiohttp.ClientSession._request != _orig_request:
        return

    LOGGER.info("Installing aiohttp interceptor")
    aiohttp.ClientSession._request = _patched_request
