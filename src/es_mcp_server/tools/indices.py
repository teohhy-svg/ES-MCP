"""Index read-only MCP tools."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from es_mcp_server.config import Settings
from es_mcp_server.es_client import ElasticsearchService
from es_mcp_server.models.tools import (
    IndexMappingRequest,
    IndexSettingsRequest,
    ListIndicesRequest,
)
from es_mcp_server.tools.common import run_tool


def register_index_tools(
    mcp: FastMCP,
    settings: Settings,
    service: ElasticsearchService,
) -> None:
    @mcp.tool()
    def es_list_indices(
        pattern: str = "*",
        include_hidden: bool = False,
        size: int = 100,
        request_timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        """List allowed Elasticsearch indices with health, status, docs, and store size."""

        return run_tool(
            settings=settings,
            tool_name="es_list_indices",
            operation_type="index_read",
            index_or_pattern=pattern,
            action=lambda: service.list_indices(
                ListIndicesRequest(
                    pattern=pattern,
                    include_hidden=include_hidden,
                    size=size,
                    request_timeout_seconds=request_timeout_seconds,
                )
            ),
        )

    @mcp.tool()
    def es_index_mapping(
        index: str,
        request_timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        """Show mapping for an allowed Elasticsearch index or pattern."""

        return run_tool(
            settings=settings,
            tool_name="es_index_mapping",
            operation_type="index_read",
            index_or_pattern=index,
            action=lambda: service.index_mapping(
                IndexMappingRequest(index=index, request_timeout_seconds=request_timeout_seconds)
            ),
        )

    @mcp.tool()
    def es_index_settings(
        index: str,
        include_defaults: bool = False,
        request_timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        """Show settings for an allowed Elasticsearch index or pattern."""

        return run_tool(
            settings=settings,
            tool_name="es_index_settings",
            operation_type="index_read",
            index_or_pattern=index,
            action=lambda: service.index_settings(
                IndexSettingsRequest(
                    index=index,
                    include_defaults=include_defaults,
                    request_timeout_seconds=request_timeout_seconds,
                )
            ),
        )
