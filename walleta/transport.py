import json
import warnings
import urllib
import urllib.request

from decimal import Decimal
from typing import List

from walleta.models import UsageEvent
from walleta.compat import _asend


USAGE_API_URL = "https://walleta-dev.dev/api/latest/usage/usage/"
DEBIT_API_URL = "https://walleta-dev.dev/api/latest/ledger/transaction/"


def _send(url: str, payload: Any) -> None:
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req) as resp:
            # optionally read resp.read() if needed
            pass

    except urllib.error.HTTPError as e:
        warnings.warn(f"HTTPError sending usage: {e.code} {e.reason}")
    except urllib.error.URLError as e:
        warnings.warn(f"URLError sending usage: {e.reason}")


def send_usage(events: List[UsageEvent], url: Optional[str] = None) -> None:
    """Synchronous send using urllib."""
    if not events:
        return

    url = url or USAGE_API_URL
    payload = [ev.serialize() for ev in events]
    return _send(url, payload)


async def asend_usage(events: List[UsageEvent], url: Optional[str] = None) -> None:
    if not events:
        return

    url = url or USAGE_API_URL
    payload = [ev.serialize() for ev in events]
    return await _asend(url, payload)


def send_debit(token_tag: str, amount: Decimal, url: Optional[str] = None) -> None:
    url = url or DEBIT_API_URL
    payload = {
        'token_tag': token_tag,
        'amount': str(amount),
    }
    return _send(url, payload)


async def asend_debit(token_tag: str, amount: Decimal, url: Optional[str] = None) -> None:
    url = url or DEBIT_API_URL
    payload = {
        'token_tag': token_tag,
        'amount': str(amount),
    }
    return await _asend(url, payload)
