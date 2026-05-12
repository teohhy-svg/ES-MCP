"""Shard allocation MCP tools."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from es_mcp_server.config import Settings
from es_mcp_server.es_client import ElasticsearchService
from es_mcp_server.models.tools import ShardAllocationRequest
from es_mcp_server.tools.common import run_tool


def register_shard_tools(
    mcp: FastMCP,
    settings: Settings,
    service: ElasticsearchService,
) -> None:
    @mcp.tool()
    def es_shard_allocation(
        index: str | None = None,
        include_explanations: bool = True,
        request_timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        """Return shard allocation and optional unassigned shard explanations."""

        return run_tool(
            settings=settings,
            tool_name="es_shard_allocation",
            operation_type="cluster_read",
            index_or_pattern=index,
            action=lambda: service.shard_allocation(
                ShardAllocationRequest(
                    index=index,
                    include_explanations=include_explanations,
                    request_timeout_seconds=request_timeout_seconds,
                )
            ),
        )
