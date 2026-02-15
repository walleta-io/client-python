import logging
import time

from walleta import extractors
from walleta.interceptors import register
from walleta.models import UsageEvent, HttpData
from walleta.context import _get_current_context
from walleta.utils import timer


LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())


try:
    import httpx
    _original_httpx_send = httpx.Client.send
    _original_httpx_asend = httpx.AsyncClient.send

except ImportError:
    httpx = None
    _original_httpx_send = None
    _original_httpx_asend = None


def _patch_response_read(response, handler, ctx) -> None:
    orig_read = response.read
    orig_aread = response.aread

    def read(*args, **kwargs):
        chunk = orig_read(*args, **kwargs)
        if chunk:
            handler.handle_chunk(chunk)
        else:  # EOF
            event = handler.finalize()
            if event:
                ctx.add_usage(event)
        return chunk

    async def aread(*args, **kwargs):
        chunk = await orig_aread(*args, **kwargs)
        if chunk:
            handler.handle_chunk(chunk)
        else:  # EOF
            event = handler.finalize()
            if event:
                ctx.add_usage(event)
        return chunk

    response.read = read
    response.aread = aread


def _patch_response_close(response, handler, ctx) -> None:
    orig_close = response.close
    orig_aclose = response.aclose

    def close(*args, **kwargs):
        if getattr(response, '_content', None) is None:
            response.read()
        event = handler.finalize()
        if event:
            ctx.add_usage(event)
        return orig_close(*args, **kwargs)

    async def aclose(*args, **kwargs):
        if getattr(response, '_content', None) is None:
            await response.read()
        event = handler.finalize()
        if event:
            ctx.add_usage(event)
        return await orig_aclose(*args, **kwargs)

    response.close = close
    response.aclose = aclose


def _patch_httx_send(Client: Any) -> None:
    def _patched_httpx_send(self, request, *args, **kwargs):
        with timer() as t:
            response = _original_httpx_send(self, request, *args, **kwargs)

        ctx = _get_current_context()
        if not ctx:
            return response

        http_data = HttpData(
            host=str(request.url.host),
            method=request.method,
            url=str(request.url),
            request_headers=dict(request.headers),
            request_body=getattr(request, 'content', None),
            response_status=response.status_code,
            response_headers=dict(response.headers),
            duration=t.seconds,
        )
        handler = extractors.search(http_data)
        if not handler:
            return response
        _patch_response_read(response, handler, ctx)
        _patch_response_close(response, handler, ctx)
        return response

    Client.send = _patched_httpx_send


def _patch_httpx_async_send(AsyncClient: Any) -> None:
    async def _patched_httpx_asend(self, request, *args, **kwargs):
        start = time.perf_counter()
        response = await _original_httpx_asend(self, request, *args, **kwargs)
        duration = (time.perf_counter() - start)

        ctx = _get_current_context()
        if not ctx:
            return response

        http_data = HttpData(
            host=str(request.url.host),
            method=request.method,
            url=str(request.url),
            request_headers=dict(request.headers),
            request_body=getattr(request, 'content', None),
            response_status=response.status_code,
            response_headers=dict(response.headers),
            duration=duration,
        )
        handler = extractors.search(http_data)
        if not handler:
            return response
        return _patch_response(http_data, response, handler, ctx)

    AsyncClient.asend = _patched_httpx_asend


@register
def install_httpx():
    if httpx is None:
        return

    if httpx.Client.send != _original_httpx_send:
        return

    LOGGER.info('Installing httpx sync and async interceptors')
    _patch_httpx_send(httpx.Client)
    _patch_httpx_async_send(httpx.AsyncClient)
