"""Structured logging and audit helpers."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Mapping

from es_mcp_server.config import LogFormat, Settings
from es_mcp_server.security import mask_sensitive_value

LOGGER_NAME = "es_mcp_server"
STANDARD_LOG_RECORD_ATTRS = set(
    logging.LogRecord(
        name="",
        level=0,
        pathname="",
        lineno=0,
        msg="",
        args=(),
        exc_info=None,
    ).__dict__
)


class JsonFormatter(logging.Formatter):
    """Small JSON formatter to avoid a logging dependency in the server core."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for key in (
            "event",
            "request_id",
            "tool_name",
            "operation_type",
            "index_or_pattern",
            "allowed",
            "denial_reason",
            "duration_ms",
            "result_count",
            "error_type",
        ):
            if hasattr(record, key):
                payload[key] = getattr(record, key)

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        for key, value in record.__dict__.items():
            if (
                key not in STANDARD_LOG_RECORD_ATTRS
                and key not in payload
                and not key.startswith("_")
            ):
                payload[key] = value

        return json.dumps(mask_sensitive_value(payload), sort_keys=True, default=str)


def configure_logging(settings: Settings) -> None:
    """Configure root logging once for local, Docker, and MCP stdio runs."""

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(settings.log_level)

    handler = logging.StreamHandler()
    if settings.log_format is LogFormat.JSON:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        )

    root_logger.addHandler(handler)


def get_logger(name: str = LOGGER_NAME) -> logging.Logger:
    return logging.getLogger(name)


def audit_event(logger: logging.Logger, event: str, fields: Mapping[str, Any]) -> None:
    """Emit a sanitized audit event."""

    extra = {"event": event}
    masked_fields = mask_sensitive_value(dict(fields))
    if isinstance(masked_fields, dict):
        extra.update(masked_fields)
    logger.info(event, extra=extra)
