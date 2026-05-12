"""Pydantic response models for read-only MCP tools."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from es_mcp_server.models.common import StrictModel
from es_mcp_server.models.tools import HealthStatus


class ClusterHealthResponse(StrictModel):
    cluster_name: str | None = None
    status: HealthStatus
    number_of_nodes: int = 0
    number_of_data_nodes: int = 0
    active_primary_shards: int = 0
    active_shards: int = 0
    relocating_shards: int = 0
    initializing_shards: int = 0
    unassigned_shards: int = 0
    timed_out: bool = False


class NodeSummary(StrictModel):
    node_id: str
    name: str | None = None
    host: str | None = None
    roles: list[str] = Field(default_factory=list)
    jvm_heap_used_percent: int | None = None
    cpu_percent: int | None = None
    disk_available_bytes: int | None = None
    disk_total_bytes: int | None = None


class NodesSummaryResponse(StrictModel):
    nodes: list[NodeSummary]


class IndexSummary(StrictModel):
    name: str
    health: str | None = None
    status: str | None = None
    docs_count: int | None = None
    store_size: str | None = None
    creation_date: str | None = None


class ListIndicesResponse(StrictModel):
    indices: list[IndexSummary]
    truncated: bool


class SearchResponse(StrictModel):
    index: str
    took_ms: int = 0
    timed_out: bool = False
    total: int | str | None = None
    hits: list[dict[str, Any]]
    aggregations: dict[str, Any] | None = None


class MappingResponse(StrictModel):
    index: str
    mapping: dict[str, Any]


class SettingsResponse(StrictModel):
    index: str
    settings: dict[str, Any]


class RecentLogsResponse(StrictModel):
    index: str
    took_ms: int = 0
    hits: list[dict[str, Any]]


class ErrorTrendBucket(StrictModel):
    timestamp: str
    groups: dict[str, int]


class ErrorTrendsResponse(StrictModel):
    buckets: list[ErrorTrendBucket]


class SlowQueriesResponse(StrictModel):
    configured: bool
    hits: list[dict[str, Any]]


class ShardAllocationResponse(StrictModel):
    shards: list[dict[str, Any]]
    unassigned_explanations: list[dict[str, Any]]


class SnapshotStatusResponse(StrictModel):
    repositories: list[dict[str, Any]]
    snapshots: list[dict[str, Any]]
    permission_limited: bool
