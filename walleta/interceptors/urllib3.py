import logging
import time

from walleta import extractors
from walleta.extractors import ResponseHandler
from walleta.utils import timer
from walleta.interceptors import register
from walleta.models import UsageEvent, HttpData
from walleta.context import _get_current_context


LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())

_orig_urlopen = urllib3.connectionpool.HTTPConnectionPool.urlopen


def _patch_response_read(handler: ResponseHandler, response, ctx) -> None:
    orig_read = response.read

    def read(*args, **kwargs):
        chunk = orig_read(*args, **kwargs)
        if chunk:
            handler.handle_chunk(chunk)
        else:  # EOF
            event = handler.finalize()
            if event:
                cxt.add_usage(event)
        return chunk

    response.read = read

def _patch_response_close(handler: ResponseHandler, response, ctx) -> None:
    orig_close = response.close

    def close(*args, **kwargs):
        if getattr(response, '_body', None) is None:
            response.read()
        event = handler.finalize()
        if event:
            ctx.send_usage(event)
        return orig_close(*args, **kwargs)


def _patched_urlopen(self, method, url, *args, **kwargs):
    ctx = _get_current_context()
    with timer() as t:
        response = _orig_urlopen(self, method, url, *args, **kwargs)

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
        duration=duration,
    )
    handler = extractors.search(http_data)
    if handler is None:
        return response
    _patch_response_read(handler, response, ctx)
    _patch_response_close(handler, response, ctx)
    return response


@register
def install_urllib3():
    if urllib3.connectionpool.HTTPConnectionPool.urlopen == _patched_urlopen:
        return

    LOGGER.info('Installing urllib3 sync interceptor')
    urllib3.connectionpool.HTTPConnectionPool.urlopen = _patched_urlopen
