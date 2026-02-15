import json
import urllib3
import warnings
from decimal import Decimal
from typing import List

from walleta.models import UsageEvent
from walleta.compat import _asend


USAGE_API_URL = "https://walleta-dev.dev/api/latest/usage/usage/"
DEBIT_API_URL = "https://walleta-dev.dev/api/latest/ledger/transaction/"


def send_usage(events: List[UsageEvent]) -> None:
    """Synchronous send using urllib3."""
    if not events:
        return

    payload = [ev.serialize() for ev in events]
    client = urllib3.PoolManager()
    client.request(
        "POST",
        USAGE_API_URL,
        body=json.dumps(payload),
        headers={"Content-Type": "application/json"},
    )


async def asend_usage(events: List[UsageEvent]) -> None:
    if not events:
        return

    payload = [ev.serialize() for ev in events]
    return await _asend(USAGE_API_URL, payload)


def send_debit(token_tag: str, amount: Decimal) -> None:
    payload = {
        'token_tag': token_tag,
        'amount': str(amount),
    }
    client = urllib3.PoolManager()
    client.request(
        "POST",
        DEBIT_API_URL,
        body=json.dumps(payload),
        headers={"Content-Type": "application/json"},
    )


async def asend_debit(token_tag: str, amount: Decimal) -> None:
    payload = {
        'token_tag': token_tag,
        'amount': str(amount),
    }
    return await _asend(DEBIT_API_URL, payload)
