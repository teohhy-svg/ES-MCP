"""Read-only Kibana API client and service methods."""

from __future__ import annotations

import json
from typing import Any, cast

import httpx

from es_mcp_server.config import Settings
from es_mcp_server.models.kibana import (
    KibanaAgentRequest,
    KibanaCaseActivityRequest,
    KibanaCaseRequest,
    KibanaDashboardReferencesRequest,
    KibanaDashboardReferencesResponse,
    KibanaDashboardRequest,
    KibanaDashboardResponse,
    KibanaDashboardSummary,
    KibanaFleetAgentsRequest,
    KibanaListCasesRequest,
    KibanaListDashboardsRequest,
    KibanaListDashboardsResponse,
    KibanaListRulesRequest,
    KibanaListWorkflowsRequest,
    KibanaRuleQueryRequest,
    KibanaRuleRequest,
    KibanaSpaceRequest,
    KibanaSpacesRequest,
    KibanaSpacesResponse,
    KibanaStatusRequest,
    KibanaStatusResponse,
    KibanaWorkflowExecutionsRequest,
    KibanaWorkflowRequest,
)
from es_mcp_server.security import (
    SecurityError,
    cap_kibana_timeout,
    cap_size,
    mask_sensitive_value,
    validate_kibana_filter_values,
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

    def alerting_health(self, request: KibanaSpaceRequest) -> dict[str, Any]:
        return self._get_dict(
            f"{self._space_path(request.space_id)}/api/alerting/_health",
            request.request_timeout_seconds,
        )

    def rule_types(self, request: KibanaSpaceRequest) -> dict[str, Any]:
        response = self._get(
            f"{self._space_path(request.space_id)}/api/alerting/rule_types",
            request.request_timeout_seconds,
        )
        if not isinstance(response, list):
            raise SecurityError("Unexpected Kibana rule types response")
        return {"rule_types": response}

    def list_rules(self, request: KibanaListRulesRequest) -> dict[str, Any]:
        size = cap_size(request.size, self.settings)
        params: dict[str, Any] = {
            "per_page": size,
            "page": request.page,
        }
        search = validate_kibana_search_text(request.search)
        if search:
            params.update(
                {
                    "search": search,
                    "search_fields": "name",
                    "default_search_operator": "AND",
                }
            )
        return self._get_dict(
            f"{self._space_path(request.space_id)}/api/alerting/rules/_find",
            request.request_timeout_seconds,
            params=params,
        )

    def get_rule(self, request: KibanaRuleRequest) -> dict[str, Any]:
        rule_id = validate_kibana_saved_object_id(request.object_id)
        return self._get_dict(
            f"{self._space_path(request.space_id)}/api/alerting/rule/{rule_id}",
            request.request_timeout_seconds,
        )

    def rule_query(self, request: KibanaRuleQueryRequest) -> dict[str, Any]:
        rule_id = validate_kibana_saved_object_id(request.object_id)
        params: dict[str, Any] = {"mode": request.mode}
        if request.alert_id:
            params["alert_id"] = validate_kibana_saved_object_id(request.alert_id)
        return self._get_dict(
            f"{self._space_path(request.space_id)}/api/alerting/rule/{rule_id}/query_inspector",
            request.request_timeout_seconds,
            params=params,
        )

    def connectors(self, request: KibanaSpaceRequest) -> dict[str, Any]:
        response = self._get(
            f"{self._space_path(request.space_id)}/api/actions/connectors",
            request.request_timeout_seconds,
        )
        if not isinstance(response, list):
            raise SecurityError("Unexpected Kibana connectors response")
        return {"connectors": cast(list[dict[str, Any]], mask_sensitive_value(response))}

    def list_cases(self, request: KibanaListCasesRequest) -> dict[str, Any]:
        size = cap_size(request.size, self.settings)
        params: dict[str, Any] = {
            "perPage": size,
            "page": request.page,
            "sortField": "updatedAt",
            "sortOrder": "desc",
        }
        search = validate_kibana_search_text(request.search)
        if search:
            params.update(
                {
                    "search": search,
                    "searchFields": "title",
                    "defaultSearchOperator": "AND",
                }
            )
        if request.owner:
            params["owner"] = request.owner.value
        if request.status:
            params["status"] = request.status.value
        if request.severity:
            params["severity"] = request.severity.value
        tags = validate_kibana_filter_values(request.tags)
        if tags:
            params["tags"] = tags
        return self._get_dict(
            f"{self._space_path(request.space_id)}/api/cases/_find",
            request.request_timeout_seconds,
            params=params,
        )

    def get_case(self, request: KibanaCaseRequest) -> dict[str, Any]:
        case_id = validate_kibana_saved_object_id(request.object_id)
        return self._get_dict(
            f"{self._space_path(request.space_id)}/api/cases/{case_id}",
            request.request_timeout_seconds,
        )

    def case_alerts(self, request: KibanaCaseRequest) -> dict[str, Any]:
        case_id = validate_kibana_saved_object_id(request.object_id)
        response = self._get(
            f"{self._space_path(request.space_id)}/api/cases/{case_id}/alerts",
            request.request_timeout_seconds,
        )
        if isinstance(response, list):
            return {"alerts": mask_sensitive_value(response)}
        if isinstance(response, dict):
            return cast(dict[str, Any], mask_sensitive_value(response))
        raise SecurityError("Unexpected Kibana case alerts response")

    def case_activity(self, request: KibanaCaseActivityRequest) -> dict[str, Any]:
        case_id = validate_kibana_saved_object_id(request.object_id)
        return self._get_dict(
            f"{self._space_path(request.space_id)}/api/cases/{case_id}/user_actions/_find",
            request.request_timeout_seconds,
            params={
                "page": request.page,
                "perPage": cap_size(request.size, self.settings),
                "sortOrder": request.sort_order,
            },
        )

    def list_workflows(self, request: KibanaListWorkflowsRequest) -> dict[str, Any]:
        params: dict[str, Any] = {
            "size": cap_size(request.size, self.settings),
            "page": request.page,
            "managed": request.managed.value,
        }
        query = validate_kibana_search_text(request.query)
        if query:
            params["query"] = query
        if request.enabled is not None:
            params["enabled"] = str(request.enabled).lower()
        tags = validate_kibana_filter_values(request.tags)
        if tags:
            params["tags"] = tags
        return self._get_dict(
            f"{self._space_path(request.space_id)}/api/workflows",
            request.request_timeout_seconds,
            params=params,
        )

    def get_workflow(self, request: KibanaWorkflowRequest) -> dict[str, Any]:
        workflow_id = validate_kibana_saved_object_id(request.object_id)
        return self._get_dict(
            f"{self._space_path(request.space_id)}/api/workflows/workflow/{workflow_id}",
            request.request_timeout_seconds,
        )

    def workflow_executions(
        self,
        request: KibanaWorkflowExecutionsRequest,
    ) -> dict[str, Any]:
        workflow_id = validate_kibana_saved_object_id(request.object_id)
        params: dict[str, Any] = {
            "size": cap_size(request.size, self.settings),
            "page": request.page,
            "omitStepRuns": str(request.omit_step_runs).lower(),
        }
        if request.status:
            params["statuses"] = request.status.value
        return self._get_dict(
            (
                f"{self._space_path(request.space_id)}/api/workflows/workflow/"
                f"{workflow_id}/executions"
            ),
            request.request_timeout_seconds,
            params=params,
        )

    def workflow_connectors(self, request: KibanaSpaceRequest) -> dict[str, Any]:
        return self._get_dict(
            f"{self._space_path(request.space_id)}/api/workflows/connectors",
            request.request_timeout_seconds,
        )

    def ai_agents(self, request: KibanaSpaceRequest) -> dict[str, Any]:
        return self._get_dict(
            f"{self._space_path(request.space_id)}/api/agent_builder/agents",
            request.request_timeout_seconds,
        )

    def get_ai_agent(self, request: KibanaAgentRequest) -> dict[str, Any]:
        agent_id = validate_kibana_saved_object_id(request.object_id)
        return self._get_dict(
            f"{self._space_path(request.space_id)}/api/agent_builder/agents/{agent_id}",
            request.request_timeout_seconds,
        )

    def ai_tools(self, request: KibanaSpaceRequest) -> dict[str, Any]:
        return self._get_dict(
            f"{self._space_path(request.space_id)}/api/agent_builder/tools",
            request.request_timeout_seconds,
        )

    def fleet_agents(self, request: KibanaFleetAgentsRequest) -> dict[str, Any]:
        params: dict[str, Any] = {
            "perPage": cap_size(request.size, self.settings),
            "page": request.page,
            "showInactive": str(request.show_inactive).lower(),
            "withMetrics": str(request.with_metrics).lower(),
            "getStatusSummary": str(request.get_status_summary).lower(),
        }
        kuery = validate_kibana_search_text(request.kuery)
        if kuery:
            params["kuery"] = kuery
        return self._get_dict(
            f"{self._space_path(request.space_id)}/api/fleet/agents",
            request.request_timeout_seconds,
            params=params,
        )

    def capability_report(self, request: KibanaSpaceRequest) -> dict[str, Any]:
        prefix = self._space_path(request.space_id)
        probes = {
            "alerting": (f"{prefix}/api/alerting/_health", None),
            "rules": (f"{prefix}/api/alerting/rules/_find", {"per_page": 1}),
            "connectors": (f"{prefix}/api/actions/connectors", None),
            "cases": (f"{prefix}/api/cases/_find", {"perPage": 1}),
            "workflows": (f"{prefix}/api/workflows", {"size": 1, "page": 1}),
            "agent_builder": (f"{prefix}/api/agent_builder/agents", None),
            "fleet_agents": (f"{prefix}/api/fleet/agents", {"perPage": 1}),
        }
        return {
            "space_id": self._effective_space(request.space_id),
            "features": {
                name: self._probe(path, request.request_timeout_seconds, params=params)
                for name, (path, params) in probes.items()
            },
            "note": (
                "available means the configured principal can read the endpoint; "
                "permission_denied, unavailable, and error require separate follow-up."
            ),
        }

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

    def _get_dict(
        self,
        path: str,
        timeout: float | None,
        *,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        response = self._get(path, timeout, params=params)
        if not isinstance(response, dict):
            raise SecurityError("Unexpected Kibana object response")
        return cast(dict[str, Any], mask_sensitive_value(response))

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
        return cast(dict[str, Any] | list[dict[str, Any]], response.json())

    def _probe(
        self,
        path: str,
        timeout: float | None,
        *,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        try:
            response = self.client.get(
                path,
                params=params,
                timeout=cap_kibana_timeout(timeout, self.settings),
            )
        except httpx.HTTPError as exc:
            return {"status": "error", "detail": str(mask_sensitive_value(str(exc)))}
        if 200 <= response.status_code < 300:
            status = "available"
        elif response.status_code in {401, 403}:
            status = "permission_denied"
        elif response.status_code == 404:
            status = "unavailable"
        else:
            status = "error"
        return {"status": status, "http_status": response.status_code}

    def _effective_space(self, space_id: str | None) -> str | None:
        return validate_kibana_space_id(space_id or self.settings.kibana_space_id)

    def _space_path(self, space_id: str | None) -> str:
        return self._space_prefix(self._effective_space(space_id))

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
