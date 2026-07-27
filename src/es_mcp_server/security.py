"""Shared security primitives for validation, masking, and safe errors."""

from __future__ import annotations

import fnmatch
import re
from collections.abc import Mapping, Sequence
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from es_mcp_server.config import Settings

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
_FIELD_RE = re.compile(r"^[A-Za-z0-9_@.*-]+$")
_KIBANA_ID_RE = re.compile(r"^[A-Za-z0-9_.:@-]+$")
_KIBANA_SPACE_RE = re.compile(r"^[a-z0-9_-]+$")
_REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
_SORT_RE = re.compile(r"^[A-Za-z0-9_@.-]+(?::(asc|desc))?$")
MAX_KIBANA_QUERY_LENGTH = 256
MAX_KIBANA_FILTER_VALUES = 50

BLOCKED_DSL_KEYS = {
    "collapse",
    "explain",
    "function_score",
    "knn",
    "more_like_this",
    "percolate",
    "profile",
    "query_string",
    "regexp",
    "runtime_mappings",
    "script",
    "script_fields",
    "script_score",
    "suggest",
    "wildcard",
}

ALLOWED_TOP_LEVEL_DSL_KEYS = {
    "_source",
    "aggs",
    "aggregations",
    "query",
    "sort",
    "track_total_hits",
}

ALLOWED_QUERY_CLAUSES = {
    "bool",
    "exists",
    "ids",
    "match",
    "multi_match",
    "prefix",
    "range",
    "simple_query_string",
    "term",
    "terms",
}

ALLOWED_BOOL_KEYS = {
    "boost",
    "filter",
    "minimum_should_match",
    "must",
    "must_not",
    "should",
}

ALLOWED_AGG_TYPES = {"date_histogram", "terms"}


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


def cap_size(size: int, settings: Settings) -> int:
    if size < 1:
        raise SecurityError("size must be at least 1")
    return min(size, settings.max_result_size)


def cap_timeout(timeout: float | None, settings: Settings) -> float:
    effective = settings.request_timeout_seconds if timeout is None else timeout
    if effective <= 0:
        raise SecurityError("request timeout must be greater than zero")
    return min(effective, settings.max_timeout_seconds)


def cap_kibana_timeout(timeout: float | None, settings: Settings) -> float:
    effective = settings.kibana_request_timeout_seconds if timeout is None else timeout
    if effective <= 0:
        raise SecurityError("request timeout must be greater than zero")
    return min(effective, settings.max_timeout_seconds)


def validate_index_pattern(
    index: str,
    settings: Settings,
    *,
    allow_wildcards: bool = True,
    include_hidden: bool = False,
) -> str:
    candidate = _clean_index_value(index)
    if not allow_wildcards and ("*" in candidate or "?" in candidate):
        raise SecurityError("wildcards are not allowed for this operation")
    if not include_hidden and candidate.startswith("."):
        raise SecurityError("hidden and system indices are blocked by default")
    if any(fnmatch.fnmatchcase(candidate, pattern) for pattern in settings.index_denylist):
        raise SecurityError("index is denied by ES_INDEX_DENYLIST")
    if not any(_is_allowed_by_pattern(candidate, pattern) for pattern in settings.index_allowlist):
        raise SecurityError("index is not allowed by ES_INDEX_ALLOWLIST")
    return candidate


def validate_exact_index_name(
    index: str,
    settings: Settings,
    *,
    include_hidden: bool = False,
) -> str:
    return validate_index_pattern(
        index,
        settings,
        allow_wildcards=False,
        include_hidden=include_hidden,
    )


def validate_field_name(field: str) -> str:
    if not field or not _FIELD_RE.fullmatch(field):
        raise SecurityError(f"invalid field name: {field!r}")
    return field


def validate_field_names(fields: Sequence[str] | None) -> list[str] | None:
    if fields is None:
        return None
    return [validate_field_name(field) for field in fields]


def validate_repository_name(repository: str) -> str:
    candidate = repository.strip()
    if not candidate or candidate != repository or not _REPOSITORY_RE.fullmatch(candidate):
        raise SecurityError("repository name contains unsupported characters")
    return candidate


def validate_kibana_space_id(space_id: str | None) -> str | None:
    if space_id is None:
        return None
    candidate = space_id.strip()
    if candidate in {"", "default"}:
        return "default"
    if candidate != space_id or not _KIBANA_SPACE_RE.fullmatch(candidate):
        raise SecurityError("Kibana space id contains unsupported characters")
    return candidate


def validate_kibana_saved_object_id(saved_object_id: str) -> str:
    candidate = saved_object_id.strip()
    if not candidate or candidate != saved_object_id:
        raise SecurityError("Kibana saved object id is required")
    if "/" in candidate or "\\" in candidate or ".." in candidate:
        raise SecurityError("Kibana saved object id contains unsupported path characters")
    if not _KIBANA_ID_RE.fullmatch(candidate):
        raise SecurityError("Kibana saved object id contains unsupported characters")
    return candidate


def validate_kibana_search_text(search: str | None) -> str | None:
    if search is None:
        return None
    candidate = search.strip()
    if not candidate:
        return None
    if len(candidate) > MAX_KIBANA_QUERY_LENGTH:
        raise SecurityError("Kibana search text is too long")
    if any(char in candidate for char in ("\x00", "\n", "\r")):
        raise SecurityError("Kibana search text contains unsupported control characters")
    if "*" in candidate or "?" in candidate:
        raise SecurityError("Kibana search text does not allow wildcard characters")
    return candidate


def validate_kibana_filter_values(values: Sequence[str] | None) -> list[str]:
    if values is None:
        return []
    if len(values) > MAX_KIBANA_FILTER_VALUES:
        raise SecurityError("too many Kibana filter values")
    normalized = []
    for value in values:
        candidate = validate_kibana_search_text(value)
        if candidate:
            normalized.append(candidate)
    return normalized


def validate_sort(sort: Sequence[str] | None) -> list[str] | None:
    if sort is None:
        return None
    normalized: list[str] = []
    for item in sort:
        if not _SORT_RE.fullmatch(item):
            raise SecurityError(f"invalid sort expression: {item!r}")
        normalized.append(item)
    return normalized


def validate_limited_dsl(dsl: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(dsl, Mapping) or not dsl:
        raise SecurityError("DSL body must be a non-empty object")
    _reject_blocked_keys(dsl)

    unknown_top_level = set(dsl) - ALLOWED_TOP_LEVEL_DSL_KEYS
    if unknown_top_level:
        raise SecurityError(f"unsupported top-level DSL keys: {sorted(unknown_top_level)}")

    if "query" in dsl:
        _validate_query_clause(dsl["query"])
    if "sort" in dsl:
        _validate_sort_clause(dsl["sort"])
    if "_source" in dsl:
        _validate_source_filter(dsl["_source"])
    for agg_key in ("aggs", "aggregations"):
        if agg_key in dsl:
            _validate_aggs(dsl[agg_key])

    return dict(dsl)


def _clean_index_value(index: str) -> str:
    candidate = index.strip()
    if not candidate:
        raise SecurityError("index is required")
    if candidate != index or any(char.isspace() for char in candidate):
        raise SecurityError("index must not contain whitespace")
    if "," in candidate:
        raise SecurityError("comma-separated index lists are disabled")
    if any(char in candidate for char in ('\\', '/', ':', '"', "<", ">", "|", "#")):
        raise SecurityError("index contains unsupported characters")
    if ".." in candidate:
        raise SecurityError("index must not contain path traversal markers")
    return candidate


def _is_allowed_by_pattern(index: str, pattern: str) -> bool:
    return pattern == "*" or index == pattern or fnmatch.fnmatchcase(index, pattern)


def _reject_blocked_keys(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key) in BLOCKED_DSL_KEYS:
                raise SecurityError(f"unsupported or dangerous DSL clause: {key}")
            _reject_blocked_keys(item)
    elif isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        for item in value:
            _reject_blocked_keys(item)


def _validate_query_clause(value: Any) -> None:
    if not isinstance(value, Mapping) or not value:
        raise SecurityError("query must be a non-empty object")
    for clause, clause_body in value.items():
        if clause not in ALLOWED_QUERY_CLAUSES:
            raise SecurityError(f"unsupported query clause: {clause}")
        if clause == "bool":
            _validate_bool_clause(clause_body)


def _validate_bool_clause(value: Any) -> None:
    if not isinstance(value, Mapping):
        raise SecurityError("bool query must be an object")
    unknown_bool_keys = set(value) - ALLOWED_BOOL_KEYS
    if unknown_bool_keys:
        raise SecurityError(f"unsupported bool keys: {sorted(unknown_bool_keys)}")
    for key in ("must", "filter", "should", "must_not"):
        if key not in value:
            continue
        item = value[key]
        if isinstance(item, Mapping):
            _validate_query_clause(item)
        elif isinstance(item, Sequence) and not isinstance(item, (bytes, bytearray, str)):
            for child in item:
                _validate_query_clause(child)
        else:
            raise SecurityError(f"bool.{key} must be an object or list of objects")


def _validate_sort_clause(value: Any) -> None:
    if isinstance(value, str):
        validate_sort([value])
        return
    if not isinstance(value, Sequence) or isinstance(value, (bytes, bytearray)):
        raise SecurityError("sort must be a string or list")
    for item in value:
        if isinstance(item, str):
            validate_sort([item])
        elif isinstance(item, Mapping):
            for field in item:
                validate_field_name(str(field))
        else:
            raise SecurityError("sort entries must be strings or field objects")


def _validate_source_filter(value: Any) -> None:
    if isinstance(value, bool):
        return
    if isinstance(value, str):
        validate_field_name(value)
        return
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        validate_field_names([str(item) for item in value])
        return
    if isinstance(value, Mapping):
        for key in ("includes", "excludes"):
            if key in value:
                raw_fields = value[key]
                if not isinstance(raw_fields, Sequence) or isinstance(raw_fields, str):
                    raise SecurityError(f"_source.{key} must be a list")
                validate_field_names([str(item) for item in raw_fields])
        return
    raise SecurityError("_source must be a bool, field, field list, or source filter object")


def _validate_aggs(value: Any) -> None:
    if not isinstance(value, Mapping):
        raise SecurityError("aggregations must be an object")
    for agg_name, agg_body in value.items():
        validate_field_name(str(agg_name))
        if not isinstance(agg_body, Mapping):
            raise SecurityError("aggregation body must be an object")
        agg_types = set(agg_body) & ALLOWED_AGG_TYPES
        if len(agg_types) != 1:
            raise SecurityError("aggregation must contain exactly one allowed aggregation type")
        unknown_keys = set(agg_body) - ALLOWED_AGG_TYPES - {"aggs", "aggregations"}
        if unknown_keys:
            raise SecurityError(f"unsupported aggregation keys: {sorted(unknown_keys)}")
        for nested_key in ("aggs", "aggregations"):
            if nested_key in agg_body:
                _validate_aggs(agg_body[nested_key])
