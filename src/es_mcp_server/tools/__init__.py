"""MCP tool registration package."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from es_mcp_server.config import Settings


def register_tools(mcp: FastMCP, settings: Settings) -> None:
    """Register tools in later phases.

    Phase 3 will add read-only Elasticsearch tools. Phase 5 will add optional
    write/destructive tools behind feature flags.
    """

    _ = (mcp, settings)
