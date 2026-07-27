from __future__ import annotations

from collections.abc import Callable

import httpx

from es_mcp_server.config import Settings
from es_mcp_server.kibana_client import KibanaService
from es_mcp_server.models.kibana import (
    KibanaDashboardReferencesRequest,
    KibanaFleetAgentsRequest,
    KibanaListCasesRequest,
    KibanaListDashboardsRequest,
    KibanaListRulesRequest,
    KibanaListWorkflowsRequest,
    KibanaSpaceRequest,
    KibanaWorkflowExecutionsRequest,
)


def test_kibana_list_dashboards_normalizes_saved_objects() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/saved_objects/_find"
        assert request.url.params["type"] == "dashboard"
        return httpx.Response(
            200,
            json={
                "total": 1,
                "page": 1,
                "per_page": 20,
                "saved_objects": [
                    {
                        "id": "dash-1",
                        "type": "dashboard",
                        "updated_at": "2026-01-01T00:00:00Z",
                        "attributes": {"title": "Latency", "description": "API latency"},
                    }
                ],
            },
        )

    service = KibanaService(_client(handler), _settings())

    result = service.list_dashboards(KibanaListDashboardsRequest(search="latency"))

    assert result["total"] == 1
    assert result["dashboards"][0]["id"] == "dash-1"
    assert result["dashboards"][0]["title"] == "Latency"


def test_kibana_dashboard_references_extracts_panels() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/s/observability/api/saved_objects/dashboard/dash-1"
        return httpx.Response(
            200,
            json={
                "id": "dash-1",
                "type": "dashboard",
                "attributes": {
                    "title": "Latency",
                    "panelsJSON": (
                        '[{"panelIndex":"1","panelRefName":"panel_0",'
                        '"gridData":{"x":0,"y":0,"w":24,"h":15}}]'
                    ),
                },
                "references": [
                    {"name": "panel_0", "type": "lens", "id": "lens-1"},
                ],
            },
        )

    service = KibanaService(_client(handler), _settings())

    result = service.dashboard_references(
        KibanaDashboardReferencesRequest(dashboard_id="dash-1", space_id="observability")
    )

    assert result["dashboard_id"] == "dash-1"
    assert result["panels"][0]["panel_type"] == "lens"
    assert result["panels"][0]["saved_object_id"] == "lens-1"


def test_kibana_list_rules_uses_public_alerting_api_and_caps_size() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/s/observability/api/alerting/rules/_find"
        assert request.url.params["per_page"] == "5"
        assert request.url.params["search"] == "latency"
        return httpx.Response(200, json={"data": [{"id": "rule-1"}], "total": 1})

    settings = _settings(max_result_size=5)
    service = KibanaService(_client(handler), settings)

    result = service.list_rules(
        KibanaListRulesRequest(search="latency", space_id="observability", size=100)
    )

    assert result["data"][0]["id"] == "rule-1"


def test_kibana_list_cases_applies_operational_filters() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/cases/_find"
        assert request.url.params["owner"] == "observability"
        assert request.url.params["status"] == "open"
        assert request.url.params["severity"] == "high"
        return httpx.Response(200, json={"cases": [], "total": 0})

    service = KibanaService(_client(handler), _settings())
    result = service.list_cases(
        KibanaListCasesRequest(
            owner="observability",
            status="open",
            severity="high",
            tags=["production"],
        )
    )

    assert result["total"] == 0


def test_kibana_workflow_execution_endpoint_is_versioned_public_api() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/workflows/workflow/workflow-1/executions"
        assert request.url.params["statuses"] == "failed"
        assert request.url.params["omitStepRuns"] == "true"
        return httpx.Response(200, json={"results": [{"id": "exec-1"}], "total": 1})

    service = KibanaService(_client(handler), _settings())
    result = service.workflow_executions(
        KibanaWorkflowExecutionsRequest(object_id="workflow-1", status="failed")
    )

    assert result["results"][0]["id"] == "exec-1"


def test_kibana_list_workflows_masks_nested_secrets() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/workflows"
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "id": "workflow-1",
                        "definition": {"api_key": "must-not-leak"},
                    }
                ],
                "total": 1,
            },
        )

    service = KibanaService(_client(handler), _settings())
    result = service.list_workflows(KibanaListWorkflowsRequest())

    assert result["results"][0]["definition"]["api_key"] == "***"


def test_kibana_fleet_agent_list_is_bounded() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/fleet/agents"
        assert request.url.params["perPage"] == "3"
        assert request.url.params["withMetrics"] == "true"
        return httpx.Response(200, json={"items": [], "total": 0})

    service = KibanaService(_client(handler), _settings(max_result_size=3))
    result = service.fleet_agents(KibanaFleetAgentsRequest(size=50, with_metrics=True))

    assert result["total"] == 0


def test_kibana_capability_report_distinguishes_access_states() -> None:
    statuses = {
        "/api/alerting/_health": 200,
        "/api/alerting/rules/_find": 403,
        "/api/actions/connectors": 200,
        "/api/cases/_find": 200,
        "/api/workflows": 404,
        "/api/agent_builder/agents": 404,
        "/api/fleet/agents": 503,
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(statuses[request.url.path], json={})

    service = KibanaService(_client(handler), _settings())
    result = service.capability_report(KibanaSpaceRequest())

    assert result["features"]["alerting"]["status"] == "available"
    assert result["features"]["rules"]["status"] == "permission_denied"
    assert result["features"]["workflows"]["status"] == "unavailable"
    assert result["features"]["fleet_agents"]["status"] == "error"


def _settings(**overrides: object) -> Settings:
    return Settings(
        _env_file=None,
        elasticsearch_url="http://localhost:9200",
        kibana_url="http://localhost:5601",
        **overrides,
    )


def _client(handler: Callable[[httpx.Request], httpx.Response]) -> httpx.Client:
    return httpx.Client(base_url="http://localhost:5601", transport=httpx.MockTransport(handler))
