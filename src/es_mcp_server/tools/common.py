"""Shared helpers for MCP tool handlers."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any
from uuid import uuid4

from pydantic import ValidationError

from es_mcp_server.audit import audit_event, get_logger
from es_mcp_server.config import Settings
from es_mcp_server.models.common import ErrorResponse, ErrorType
from es_mcp_server.security import SecurityError, mask_sensitive_value


def run_tool(
    *,
    settings: Settings,
    tool_name: str,
    operation_type: str,
    index_or_pattern: str | None,
    action: Callable[[], dict[str, Any]],
) -> dict[str, Any]:
    """Run a tool with consistent audit logging and sanitized errors."""

    _ = settings
    logger = get_logger()
    request_id = str(uuid4())
    started = time.monotonic()
    audit_event(
        logger,
        "tool_call_started",
        {
            "request_id": request_id,
            "tool_name": tool_name,
            "operation_type": operation_type,
            "index_or_pattern": index_or_pattern,
        },
    )
    try:
        result = action()
    except ValidationError as exc:
        return _error(
            request_id,
            started,
            tool_name,
            operation_type,
            index_or_pattern,
            ErrorType.VALIDATION_ERROR,
            str(exc),
        )
    except SecurityError as exc:
        return _error(
            request_id,
            started,
            tool_name,
            operation_type,
            index_or_pattern,
            ErrorType.SECURITY_DENIED,
            str(exc),
        )
    except TimeoutError as exc:
        return _error(
            request_id,
            started,
            tool_name,
            operation_type,
            index_or_pattern,
            ErrorType.TIMEOUT,
            str(exc),
        )
    except Exception as exc:  # pragma: no cover - concrete errors depend on ES/runtime
        return _error(
            request_id,
            started,
            tool_name,
            operation_type,
            index_or_pattern,
            ErrorType.ELASTICSEARCH_ERROR,
            str(mask_sensitive_value(str(exc))),
        )

    audit_event(
        logger,
        "tool_call_succeeded",
        {
            "request_id": request_id,
            "tool_name": tool_name,
            "operation_type": operation_type,
            "index_or_pattern": index_or_pattern,
            "duration_ms": _duration_ms(started),
            "result_count": _result_count(result),
        },
    )
    return result


def _error(
    request_id: str,
    started: float,
    tool_name: str,
    operation_type: str,
    index_or_pattern: str | None,
    error_type: ErrorType,
    message: str,
) -> dict[str, Any]:
    safe_message = str(mask_sensitive_value(message))
    audit_event(
        get_logger(),
        "tool_call_failed" if error_type is not ErrorType.SECURITY_DENIED else "tool_call_denied",
        {
            "request_id": request_id,
            "tool_name": tool_name,
            "operation_type": operation_type,
            "index_or_pattern": index_or_pattern,
            "duration_ms": _duration_ms(started),
            "error_type": error_type.value,
            "denial_reason": safe_message if error_type is ErrorType.SECURITY_DENIED else None,
        },
    )
    return {
        "error": ErrorResponse(
            error_type=error_type,
            message=safe_message,
            request_id=request_id,
        ).model_dump(mode="json")
    }


def _duration_ms(started: float) -> int:
    return int((time.monotonic() - started) * 1000)


def _result_count(result: dict[str, Any]) -> int | None:
    for key in (
        "hits",
        "indices",
        "nodes",
        "shards",
        "snapshots",
        "repositories",
        "buckets",
        "spaces",
        "dashboards",
        "panels",
        "data",
        "connectors",
        "cases",
        "results",
        "rule_types",
        "items",
    ):
        value = result.get(key)
        if isinstance(value, list):
            return len(value)
    return None
