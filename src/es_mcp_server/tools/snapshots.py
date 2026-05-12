"""Snapshot status MCP tools."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from es_mcp_server.config import Settings
from es_mcp_server.es_client import ElasticsearchService
from es_mcp_server.models.tools import SnapshotStatusRequest
from es_mcp_server.tools.common import run_tool


def register_snapshot_tools(
    mcp: FastMCP,
    settings: Settings,
    service: ElasticsearchService,
) -> None:
    @mcp.tool()
    def es_snapshot_status(
        repository: str | None = None,
        include_snapshots: bool = True,
        size: int = 20,
        request_timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        """Show snapshot repositories and recent snapshot status when permitted."""

        return run_tool(
            settings=settings,
            tool_name="es_snapshot_status",
            operation_type="cluster_read",
            index_or_pattern=None,
            action=lambda: service.snapshot_status(
                SnapshotStatusRequest(
                    repository=repository,
                    include_snapshots=include_snapshots,
                    size=size,
                    request_timeout_seconds=request_timeout_seconds,
                )
            ),
        )
