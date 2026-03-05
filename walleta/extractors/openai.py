import re

from typing import Any, Iterable

from walleta.models import HttpData, UsageEventContext
from walleta.extractors import ResponseHandler, register


TOKEN_PATTERNS = [
    re.compile(r'"(%s)":\s*(\d+)' % token_name)
    for token_name in (
        'input', 'output', 'cached'
    )
]

@register
class OpenAIResponseHandler(ResponseHandler):
    def __init__(self, http_data: HttpData) -> None:
        super().__init__(http_data)
        self._remaining: bytes = b''
        self._usage_data: dict[str, Any] = {}
        self._finalized = False

    def _process_lines(self, lines: Iterable[bytes]) -> None:
        for line in lines:
            decoded = line.decode(errors='ignore')
            if not decoded:
                continue
            self._usage_data.update({
                m.group(1): int(m.group(2))
                for pattern in TOKEN_PATTERNS
                for m in (pattern.search(decoded),)
                if m
            })

    def handle_chunk(self, chunk: bytes) -> None:
        data = self._remaining + chunk
        lines = data.split(b'\n')
        self._remaining = lines.pop(-1)
        self._process_lines(lines)

    def finalize(self):
        if self._finalized:
            return
        self._finalized = True

        if self._remaining:
            self._process_lines([self._remaining])

        if not self._usage_data:
            return

        event = UsageEventContext(
            provider='openai',
            usage=self._usage_data,
            http_data=self.http_data,
        )
        return event
