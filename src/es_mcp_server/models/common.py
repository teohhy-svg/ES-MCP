"""Shared Pydantic model primitives."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class ErrorType(str, Enum):
    VALIDATION_ERROR = "validation_error"
    SECURITY_DENIED = "security_denied"
    ELASTICSEARCH_ERROR = "elasticsearch_error"
    PERMISSION_LIMITED = "permission_limited"
    TIMEOUT = "timeout"


class ErrorResponse(StrictModel):
    error_type: ErrorType
    message: str = Field(min_length=1)
    request_id: str | None = None
