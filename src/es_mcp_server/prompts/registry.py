"""Prompt registration placeholders for Phase 4."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from es_mcp_server.config import Settings


def register_prompts(mcp: FastMCP, settings: Settings) -> None:
    """Register prompts in Phase 4."""

    _ = (mcp, settings)
