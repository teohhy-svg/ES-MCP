"""Read-only Kibana MCP tools."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from es_mcp_server.config import Settings
from es_mcp_server.kibana_client import KibanaService
from es_mcp_server.models.kibana import (
    KibanaDashboardReferencesRequest,
    KibanaDashboardRequest,
    KibanaListDashboardsRequest,
    KibanaSpacesRequest,
    KibanaStatusRequest,
)
from es_mcp_server.tools.common import run_tool


def register_kibana_tools(
    mcp: FastMCP,
    settings: Settings,
    service: KibanaService,
) -> None:
    @mcp.tool()
    def kbn_status(request_timeout_seconds: float | None = None) -> dict[str, Any]:
        """Return Kibana operational status."""

        return run_tool(
            settings=settings,
            tool_name="kbn_status",
            operation_type="kibana_read",
            index_or_pattern=None,
            action=lambda: service.status(
                KibanaStatusRequest(request_timeout_seconds=request_timeout_seconds)
            ),
        )

    @mcp.tool()
    def kbn_spaces(
        include_authorized_purposes: bool = False,
        request_timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        """List Kibana spaces visible to the configured principal."""

        return run_tool(
            settings=settings,
            tool_name="kbn_spaces",
            operation_type="kibana_read",
            index_or_pattern=None,
            action=lambda: service.spaces(
                KibanaSpacesRequest(
                    include_authorized_purposes=include_authorized_purposes,
                    request_timeout_seconds=request_timeout_seconds,
                )
            ),
        )

    @mcp.tool()
    def kbn_list_dashboards(
        search: str | None = None,
        space_id: str | None = None,
        size: int = 20,
        page: int = 1,
        request_timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        """Search Kibana dashboards in a space."""

        return run_tool(
            settings=settings,
            tool_name="kbn_list_dashboards",
            operation_type="kibana_read",
            index_or_pattern=space_id or settings.kibana_space_id,
            action=lambda: service.list_dashboards(
                KibanaListDashboardsRequest(
                    search=search,
                    space_id=space_id,
                    size=size,
                    page=page,
                    request_timeout_seconds=request_timeout_seconds,
                )
            ),
        )

    @mcp.tool()
    def kbn_get_dashboard(
        dashboard_id: str,
        space_id: str | None = None,
        request_timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        """Fetch a Kibana dashboard saved object by ID."""

        return run_tool(
            settings=settings,
            tool_name="kbn_get_dashboard",
            operation_type="kibana_read",
            index_or_pattern=space_id or settings.kibana_space_id,
            action=lambda: service.get_dashboard(
                KibanaDashboardRequest(
                    dashboard_id=dashboard_id,
                    space_id=space_id,
                    request_timeout_seconds=request_timeout_seconds,
                )
            ),
        )

    @mcp.tool()
    def kbn_dashboard_references(
        dashboard_id: str,
        space_id: str | None = None,
        request_timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        """Fetch dashboard references and panel metadata for investigation."""

        return run_tool(
            settings=settings,
            tool_name="kbn_dashboard_references",
            operation_type="kibana_read",
            index_or_pattern=space_id or settings.kibana_space_id,
            action=lambda: service.dashboard_references(
                KibanaDashboardReferencesRequest(
                    dashboard_id=dashboard_id,
                    space_id=space_id,
                    request_timeout_seconds=request_timeout_seconds,
                )
            ),
        )
