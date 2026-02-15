from dataclasses import dataclass, field
from typing import Any


@dataclass
class HttpData:
    host: str = None
    method: str = None
    url: str = None
    request_headers: dict[str, Any] = field(default_factory=dict)
    request_body: bytes = None
    response_status: int
    response_headers: dict[str, Any] = field(default_factory=dict)
    duration: float = 0.0

    def serialize(self):
        metadata: dict[str, Any] = {}
        for prop_name in ('host', 'method', 'url', 'duration'):
            value = getattr(self, prop_name, None)
            if value is None:
                continue
            metadata[f'http.{prop_name}'] = value
        if self.response_status:
            metadata['http.status'] = self.response_status
        for k, v in self.request_headers.items():
            metadata[f'http.request.headers.{k}'] = v
        for k, v in self.response_headers.items():
            metadata[f'http.response.headers.{k}'] = v        
        return metadata


@dataclass
class UsageEvent:
    provider: str = None
    metadata: dict[str, Any] = field(default_factory=dict)
    usage: dict[str, Any] = field(default_factory=dict)

    def serialize(self) -> dict[str, Any]:
        return {
            'provider': self.provider,
            'metadata': self.metadata,
            'usage': self.usage,
        }


@dataclass
class UsageEventContext:
    provider: str = None
    http_data: HttpData = None
    usage: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)

    def add_context(self, data: dict[str, Any]):
        self.context.update(data)

    def to_usage_event(self) -> UsageEvent:
        metadata = {}
        if self.http_data:
            metadata.update(self.http_data.serialize())
        if self.context:
            metadata.update(self.context)
        return UsageEvent(self.provider, metadata, self.usage)
