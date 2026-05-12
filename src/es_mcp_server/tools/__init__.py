"""MCP tool registration package."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from es_mcp_server.config import Settings
from es_mcp_server.es_client import ElasticsearchService, create_elasticsearch_client
from es_mcp_server.tools.cluster import register_cluster_tools
from es_mcp_server.tools.indices import register_index_tools
from es_mcp_server.tools.observability import register_observability_tools
from es_mcp_server.tools.search import register_search_tools
from es_mcp_server.tools.shards import register_shard_tools
from es_mcp_server.tools.snapshots import register_snapshot_tools


def register_tools(mcp: FastMCP, settings: Settings) -> None:
    """Register read-only Elasticsearch tools.

    Phase 5 write/destructive tools are intentionally not registered yet.
    """

    service = ElasticsearchService(create_elasticsearch_client(settings), settings)
    register_cluster_tools(mcp, settings, service)
    register_index_tools(mcp, settings, service)
    register_search_tools(mcp, settings, service)
    register_observability_tools(mcp, settings, service)
    register_shard_tools(mcp, settings, service)
    register_snapshot_tools(mcp, settings, service)
