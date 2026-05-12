"""Safe search and limited DSL MCP tools."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from mcp.server.fastmcp import FastMCP

from es_mcp_server.config import Settings
from es_mcp_server.es_client import ElasticsearchService
from es_mcp_server.models.tools import DslSearchRequest, SearchRequest
from es_mcp_server.tools.common import run_tool


def register_search_tools(
    mcp: FastMCP,
    settings: Settings,
    service: ElasticsearchService,
) -> None:
    @mcp.tool()
    def es_search(
        index: str,
        query: str | None = None,
        match: dict[str, str | int | float | bool] | None = None,
        fields: list[str] | None = None,
        size: int = 10,
        sort: list[str] | None = None,
        timestamp_field: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        request_timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        """Search an allowed index using guarded high-level parameters."""

        return run_tool(
            settings=settings,
            tool_name="es_search",
            operation_type="search",
            index_or_pattern=index,
            action=lambda: service.search(
                SearchRequest(
                    index=index,
                    query=query,
                    match=match,
                    fields=fields,
                    size=size,
                    sort=sort,
                    timestamp_field=timestamp_field,
                    start_time=start_time,
                    end_time=end_time,
                    request_timeout_seconds=request_timeout_seconds,
                )
            ),
        )

    @mcp.tool()
    def es_dsl_search(
        index: str,
        dsl: dict[str, Any],
        size: int = 10,
        request_timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        """Search an allowed index with a limited, validated Elasticsearch DSL subset."""

        return run_tool(
            settings=settings,
            tool_name="es_dsl_search",
            operation_type="search",
            index_or_pattern=index,
            action=lambda: service.dsl_search(
                DslSearchRequest(
                    index=index,
                    dsl=dsl,
                    size=size,
                    request_timeout_seconds=request_timeout_seconds,
                )
            ),
        )
