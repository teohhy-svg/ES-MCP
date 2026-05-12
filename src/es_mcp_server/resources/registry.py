"""Resource registration placeholders for Phase 4."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from es_mcp_server.config import Settings


def register_resources(mcp: FastMCP, settings: Settings) -> None:
    """Register resources in Phase 4."""

    _ = (mcp, settings)
