"""Observability MCP tools for logs, error trends, and slow queries."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from mcp.server.fastmcp import FastMCP

from es_mcp_server.config import Settings
from es_mcp_server.es_client import ElasticsearchService
from es_mcp_server.models.tools import (
    ErrorTrendsRequest,
    RecentLogsRequest,
    SlowQueriesRequest,
)
from es_mcp_server.tools.common import run_tool


def register_observability_tools(
    mcp: FastMCP,
    settings: Settings,
    service: ElasticsearchService,
) -> None:
    @mcp.tool()
    def es_recent_logs(
        start_time: datetime,
        end_time: datetime,
        index: str | None = None,
        timestamp_field: str = "@timestamp",
        service_field: str = "service.name",
        service: str | None = None,
        severity_field: str = "log.level",
        severity: str | None = None,
        keyword: str | None = None,
        size: int = 50,
        request_timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        """Query recent logs by time range, service, severity, and keyword."""

        return run_tool(
            settings=settings,
            tool_name="es_recent_logs",
            operation_type="observability_search",
            index_or_pattern=index or settings.log_index_pattern,
            action=lambda: service.recent_logs(
                RecentLogsRequest(
                    index=index,
                    timestamp_field=timestamp_field,
                    start_time=start_time,
                    end_time=end_time,
                    service_field=service_field,
                    service=service,
                    severity_field=severity_field,
                    severity=severity,
                    keyword=keyword,
                    size=size,
                    request_timeout_seconds=request_timeout_seconds,
                )
            ),
        )

    @mcp.tool()
    def es_error_trends(
        start_time: datetime,
        end_time: datetime,
        index: str | None = None,
        timestamp_field: str = "@timestamp",
        interval: str = "5m",
        group_by: str = "service",
        service_field: str = "service.name",
        severity_field: str = "log.level",
        error_levels: list[str] | None = None,
        request_timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        """Aggregate error counts over time grouped by service, index, or severity."""

        return run_tool(
            settings=settings,
            tool_name="es_error_trends",
            operation_type="observability_aggregation",
            index_or_pattern=index or settings.log_index_pattern,
            action=lambda: service.error_trends(
                ErrorTrendsRequest(
                    index=index,
                    timestamp_field=timestamp_field,
                    start_time=start_time,
                    end_time=end_time,
                    interval=interval,
                    group_by=group_by,
                    service_field=service_field,
                    severity_field=severity_field,
                    error_levels=error_levels or ["error", "fatal", "critical"],
                    request_timeout_seconds=request_timeout_seconds,
                )
            ),
        )

    @mcp.tool()
    def es_slow_queries(
        start_time: datetime,
        end_time: datetime,
        index: str | None = None,
        timestamp_field: str = "@timestamp",
        threshold_ms: int | None = None,
        size: int = 50,
        request_timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        """Search configured Elasticsearch slow-log indices."""

        return run_tool(
            settings=settings,
            tool_name="es_slow_queries",
            operation_type="observability_search",
            index_or_pattern=index or settings.slow_log_index_pattern,
            action=lambda: service.slow_queries(
                SlowQueriesRequest(
                    index=index,
                    timestamp_field=timestamp_field,
                    start_time=start_time,
                    end_time=end_time,
                    threshold_ms=threshold_ms,
                    size=size,
                    request_timeout_seconds=request_timeout_seconds,
                )
            ),
        )
