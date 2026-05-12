"""Shared security primitives for validation, masking, and safe errors."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any
from urllib.parse import urlsplit, urlunsplit

MASK = "***"
SENSITIVE_KEY_PARTS = (
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "credential",
    "password",
    "secret",
    "token",
)

_BEARER_RE = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+")
_API_KEY_RE = re.compile(r"(?i)\bApiKey\s+[A-Za-z0-9._~+/=-]+")


class SecurityError(ValueError):
    """Raised when a request violates server safety policy."""


def mask_url_credentials(value: str) -> str:
    parsed = urlsplit(value)
    if not parsed.scheme or not parsed.netloc or not (parsed.username or parsed.password):
        return value

    host = parsed.hostname or ""
    if parsed.port:
        host = f"{host}:{parsed.port}"
    return urlunsplit(
        (parsed.scheme, f"{MASK}:{MASK}@{host}", parsed.path, parsed.query, parsed.fragment)
    )


def mask_sensitive_string(value: str) -> str:
    masked = mask_url_credentials(value)
    masked = _BEARER_RE.sub(f"Bearer {MASK}", masked)
    masked = _API_KEY_RE.sub(f"ApiKey {MASK}", masked)
    return masked


def is_sensitive_key(key: str) -> bool:
    lowered = key.lower()
    return any(part in lowered for part in SENSITIVE_KEY_PARTS)


def mask_sensitive_value(value: Any) -> Any:
    if isinstance(value, str):
        return mask_sensitive_string(value)
    if isinstance(value, Mapping):
        return {
            key: MASK if is_sensitive_key(str(key)) else mask_sensitive_value(item)
            for key, item in value.items()
        }
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        return [mask_sensitive_value(item) for item in value]
    return value
