"""Cluster and node read-only MCP tools."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from es_mcp_server.config import Settings
from es_mcp_server.es_client import ElasticsearchService
from es_mcp_server.models.tools import ClusterHealthRequest, NodesSummaryRequest
from es_mcp_server.tools.common import run_tool


def register_cluster_tools(
    mcp: FastMCP,
    settings: Settings,
    service: ElasticsearchService,
) -> None:
    @mcp.tool()
    def es_cluster_health(
        level: str = "cluster",
        request_timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        """Return Elasticsearch cluster health summary."""

        return run_tool(
            settings=settings,
            tool_name="es_cluster_health",
            operation_type="cluster_read",
            index_or_pattern=None,
            action=lambda: service.cluster_health(
                ClusterHealthRequest(
                    level=level,
                    request_timeout_seconds=request_timeout_seconds,
                )
            ),
        )

    @mcp.tool()
    def es_nodes_summary(
        include_indices: bool = False,
        request_timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        """Return basic Elasticsearch node, JVM, CPU, and disk summary."""

        return run_tool(
            settings=settings,
            tool_name="es_nodes_summary",
            operation_type="cluster_read",
            index_or_pattern=None,
            action=lambda: service.nodes_summary(
                NodesSummaryRequest(
                    include_indices=include_indices,
                    request_timeout_seconds=request_timeout_seconds,
                )
            ),
        )
