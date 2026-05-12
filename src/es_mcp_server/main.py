"""MCP server entrypoint."""

from __future__ import annotations

import os

from mcp.server.fastmcp import FastMCP

from es_mcp_server.audit import configure_logging, get_logger
from es_mcp_server.config import McpTransport, Settings, get_settings
from es_mcp_server.prompts.registry import register_prompts
from es_mcp_server.resources.registry import register_resources
from es_mcp_server.tools import register_tools


def build_server(settings: Settings | None = None) -> FastMCP:
    """Build and register the MCP server."""

    active_settings = settings or get_settings()
    configure_logging(active_settings)
    configure_fastmcp_environment(active_settings)
    logger = get_logger()
    logger.info(
        "starting_server",
        extra={
            "event": "server_starting",
            "transport": active_settings.mcp_transport.value,
            "elasticsearch_url": active_settings.masked_elasticsearch_url,
            "read_only": active_settings.read_only,
        },
    )

    server_kwargs = {}
    if active_settings.mcp_transport is McpTransport.STREAMABLE_HTTP:
        server_kwargs.update({"stateless_http": True, "json_response": True})

    mcp = FastMCP(active_settings.server_name, **server_kwargs)
    register_tools(mcp, active_settings)
    register_resources(mcp, active_settings)
    register_prompts(mcp, active_settings)
    return mcp


def main() -> None:
    settings = get_settings()
    server = build_server(settings)
    server.run(transport=settings.mcp_transport.value)


def configure_fastmcp_environment(settings: Settings) -> None:
    """Bridge ES-MCP settings into FastMCP's HTTP transport settings."""

    os.environ.setdefault("FASTMCP_TRANSPORT", settings.mcp_transport.value)
    os.environ.setdefault("FASTMCP_HOST", settings.mcp_http_host)
    os.environ.setdefault("FASTMCP_PORT", str(settings.mcp_http_port))
    os.environ.setdefault("FASTMCP_STREAMABLE_HTTP_PATH", settings.mcp_http_path)
    os.environ.setdefault("FASTMCP_STATELESS_HTTP", "true")
    os.environ.setdefault("FASTMCP_JSON_RESPONSE", "true")


if __name__ == "__main__":
    main()
