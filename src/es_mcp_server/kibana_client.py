"""Read-only Kibana API client and service methods."""

from __future__ import annotations

import json
from typing import Any

import httpx

from es_mcp_server.config import Settings
from es_mcp_server.models.kibana import (
    KibanaDashboardReferencesRequest,
    KibanaDashboardReferencesResponse,
    KibanaDashboardRequest,
    KibanaDashboardResponse,
    KibanaDashboardSummary,
    KibanaListDashboardsRequest,
    KibanaListDashboardsResponse,
    KibanaSpacesRequest,
    KibanaSpacesResponse,
    KibanaStatusRequest,
    KibanaStatusResponse,
)
from es_mcp_server.security import (
    SecurityError,
    cap_kibana_timeout,
    cap_size,
    validate_kibana_saved_object_id,
    validate_kibana_search_text,
    validate_kibana_space_id,
)


def create_kibana_http_client(settings: Settings) -> httpx.Client:
    """Create an HTTP client for Kibana read-only API calls."""

    if not settings.kibana_url:
        raise SecurityError("KIBANA_URL is required to enable Kibana tools")
    return httpx.Client(
        base_url=settings.kibana_url,
        follow_redirects=True,
        **settings.kibana_client_options(),
    )


class KibanaService:
    """Read-only Kibana operations used by MCP handlers."""

    def __init__(self, client: httpx.Client, settings: Settings) -> None:
        self.client = client
        self.settings = settings

    def status(self, request: KibanaStatusRequest) -> dict[str, Any]:
        response = self._get("/api/status", request.request_timeout_seconds)
        if not isinstance(response, dict):
            raise SecurityError("Unexpected Kibana status response")
        return KibanaStatusResponse(status=response).model_dump(mode="json")

    def spaces(self, request: KibanaSpacesRequest) -> dict[str, Any]:
        params = {}
        if request.include_authorized_purposes:
            params["include_authorized_purposes"] = "true"
        response = self._get(
            "/api/spaces/space",
            request.request_timeout_seconds,
            params=params,
        )
        if not isinstance(response, list):
            raise SecurityError("Unexpected Kibana spaces response")
        return KibanaSpacesResponse(spaces=response).model_dump(mode="json")

    def list_dashboards(self, request: KibanaListDashboardsRequest) -> dict[str, Any]:
        size = cap_size(request.size, self.settings)
        space_id = self._effective_space(request.space_id)
        params: dict[str, Any] = {
            "type": "dashboard",
            "per_page": size,
            "page": request.page,
            "fields": ["title", "description"],
        }
        search = validate_kibana_search_text(request.search)
        if search:
            params["search"] = search
            params["search_fields"] = "title"
            params["default_search_operator"] = "AND"

        response = self._get(
            f"{self._space_prefix(space_id)}/api/saved_objects/_find",
            request.request_timeout_seconds,
            params=params,
        )
        if not isinstance(response, dict):
            raise SecurityError("Unexpected Kibana dashboard list response")
        dashboards = [
            _dashboard_summary(item)
            for item in response.get("saved_objects", [])
            if item.get("type") == "dashboard"
        ]
        return KibanaListDashboardsResponse(
            dashboards=dashboards,
            total=response.get("total"),
            page=response.get("page", request.page),
            per_page=response.get("per_page", size),
        ).model_dump(mode="json")

    def get_dashboard(self, request: KibanaDashboardRequest) -> dict[str, Any]:
        dashboard = self._dashboard(request)
        return KibanaDashboardResponse(dashboard=dashboard).model_dump(mode="json")

    def dashboard_references(
        self,
        request: KibanaDashboardReferencesRequest,
    ) -> dict[str, Any]:
        dashboard = self._dashboard(request)
        references = list(dashboard.get("references", []))
        reference_by_name = {reference.get("name"): reference for reference in references}
        panels = _dashboard_panels(dashboard, reference_by_name)
        return KibanaDashboardReferencesResponse(
            dashboard_id=str(dashboard.get("id")),
            title=dashboard.get("attributes", {}).get("title"),
            references=references,
            panels=panels,
        ).model_dump(mode="json")

    def _dashboard(self, request: KibanaDashboardRequest) -> dict[str, Any]:
        dashboard_id = validate_kibana_saved_object_id(request.dashboard_id)
        space_id = self._effective_space(request.space_id)
        response = self._get(
            f"{self._space_prefix(space_id)}/api/saved_objects/dashboard/{dashboard_id}",
            request.request_timeout_seconds,
        )
        if not isinstance(response, dict):
            raise SecurityError("Unexpected Kibana dashboard response")
        return response

    def _get(
        self,
        path: str,
        timeout: float | None,
        *,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        response = self.client.get(
            path,
            params=params,
            timeout=cap_kibana_timeout(timeout, self.settings),
        )
        response.raise_for_status()
        return response.json()

    def _effective_space(self, space_id: str | None) -> str | None:
        return validate_kibana_space_id(space_id or self.settings.kibana_space_id)

    @staticmethod
    def _space_prefix(space_id: str | None) -> str:
        if not space_id or space_id == "default":
            return ""
        return f"/s/{space_id}"


def _dashboard_summary(item: dict[str, Any]) -> KibanaDashboardSummary:
    attributes = item.get("attributes", {})
    return KibanaDashboardSummary(
        id=str(item.get("id")),
        type=str(item.get("type", "dashboard")),
        title=attributes.get("title"),
        description=attributes.get("description"),
        updated_at=item.get("updated_at") or item.get("updatedAt"),
        references=list(item.get("references", [])),
    )


def _dashboard_panels(
    dashboard: dict[str, Any],
    reference_by_name: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    raw_panels = dashboard.get("attributes", {}).get("panelsJSON")
    if not raw_panels:
        return []
    try:
        parsed_panels = json.loads(raw_panels)
    except json.JSONDecodeError:
        return [{"parse_error": "dashboard panelsJSON is not valid JSON"}]

    panels = []
    for panel in parsed_panels:
        if not isinstance(panel, dict):
            continue
        reference = reference_by_name.get(panel.get("panelRefName"), {})
        panels.append(
            {
                "panel_index": panel.get("panelIndex"),
                "panel_type": panel.get("type") or reference.get("type"),
                "saved_object_id": panel.get("id") or reference.get("id"),
                "title": panel.get("title") or panel.get("embeddableConfig", {}).get("title"),
                "grid_data": panel.get("gridData"),
            }
        )
    return panels
