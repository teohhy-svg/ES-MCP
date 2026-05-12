"""Pydantic models for read-only MCP tool inputs."""

from __future__ import annotations

import re
from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import Field, field_validator, model_validator

from es_mcp_server.models.common import StrictModel

_INTERVAL_RE = re.compile(r"^[1-9][0-9]*(s|m|h|d)$")


class ClusterHealthLevel(str, Enum):
    CLUSTER = "cluster"
    INDICES = "indices"
    SHARDS = "shards"


class TrendGroupBy(str, Enum):
    SERVICE = "service"
    INDEX = "index"
    SEVERITY = "severity"


class RequestTimeoutModel(StrictModel):
    request_timeout_seconds: float | None = Field(default=None, gt=0)


class ClusterHealthRequest(RequestTimeoutModel):
    level: ClusterHealthLevel = ClusterHealthLevel.CLUSTER


class NodesSummaryRequest(RequestTimeoutModel):
    include_indices: bool = False


class ListIndicesRequest(RequestTimeoutModel):
    pattern: str = Field(default="*", min_length=1)
    include_hidden: bool = False
    size: int = Field(default=100, ge=1)


class IndexMappingRequest(RequestTimeoutModel):
    index: str = Field(min_length=1)


class IndexSettingsRequest(RequestTimeoutModel):
    index: str = Field(min_length=1)
    include_defaults: bool = False


class SearchRequest(RequestTimeoutModel):
    index: str = Field(min_length=1)
    query: str | None = Field(default=None, min_length=1)
    match: dict[str, str | int | float | bool] | None = None
    fields: list[str] | None = None
    size: int = Field(default=10, ge=1)
    sort: list[str] | None = None
    timestamp_field: str | None = Field(default=None, min_length=1)
    start_time: datetime | None = None
    end_time: datetime | None = None

    @model_validator(mode="after")
    def validate_search_shape(self) -> "SearchRequest":
        has_time_range = self.timestamp_field and (self.start_time or self.end_time)
        if not self.query and not self.match and not has_time_range:
            raise ValueError("search requires query, match, or a timestamp range")
        if (self.start_time or self.end_time) and not self.timestamp_field:
            raise ValueError("timestamp_field is required when start_time or end_time is provided")
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValueError("start_time must be before end_time")
        return self


class DslSearchRequest(RequestTimeoutModel):
    index: str = Field(min_length=1)
    dsl: dict[str, Any] = Field(min_length=1)
    size: int = Field(default=10, ge=1)


class TimeRangeRequest(RequestTimeoutModel):
    index: str | None = Field(default=None, min_length=1)
    timestamp_field: str = Field(default="@timestamp", min_length=1)
    start_time: datetime
    end_time: datetime

    @model_validator(mode="after")
    def validate_time_range(self) -> "TimeRangeRequest":
        if self.start_time >= self.end_time:
            raise ValueError("start_time must be before end_time")
        return self


class RecentLogsRequest(TimeRangeRequest):
    service_field: str = Field(default="service.name", min_length=1)
    service: str | None = Field(default=None, min_length=1)
    severity_field: str = Field(default="log.level", min_length=1)
    severity: str | None = Field(default=None, min_length=1)
    keyword: str | None = Field(default=None, min_length=1)
    size: int = Field(default=50, ge=1)


class ErrorTrendsRequest(TimeRangeRequest):
    interval: str = Field(default="5m", min_length=2)
    group_by: TrendGroupBy = TrendGroupBy.SERVICE
    service_field: str = Field(default="service.name", min_length=1)
    severity_field: str = Field(default="log.level", min_length=1)
    error_levels: list[str] = Field(default_factory=lambda: ["error", "fatal", "critical"])

    @field_validator("error_levels")
    @classmethod
    def validate_error_levels(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("error_levels must contain at least one value")
        return value

    @field_validator("interval")
    @classmethod
    def validate_interval(cls, value: str) -> str:
        if not _INTERVAL_RE.fullmatch(value):
            raise ValueError("interval must be a fixed interval such as 30s, 5m, 1h, or 1d")
        return value


class SlowQueriesRequest(TimeRangeRequest):
    threshold_ms: int | None = Field(default=None, ge=0)
    size: int = Field(default=50, ge=1)


class ShardAllocationRequest(RequestTimeoutModel):
    index: str | None = Field(default=None, min_length=1)
    include_explanations: bool = True


class SnapshotStatusRequest(RequestTimeoutModel):
    repository: str | None = Field(default=None, min_length=1)
    include_snapshots: bool = True
    size: int = Field(default=20, ge=1)


HealthStatus = Literal["green", "yellow", "red", "unknown"]
