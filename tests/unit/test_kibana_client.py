from __future__ import annotations

from collections.abc import Callable

import httpx

from es_mcp_server.config import Settings
from es_mcp_server.kibana_client import KibanaService
from es_mcp_server.models.kibana import (
    KibanaDashboardReferencesRequest,
    KibanaListDashboardsRequest,
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


def _settings() -> Settings:
    return Settings(
        _env_file=None,
        elasticsearch_url="http://localhost:9200",
        kibana_url="http://localhost:5601",
    )


def _client(handler: Callable[[httpx.Request], httpx.Response]) -> httpx.Client:
    return httpx.Client(base_url="http://localhost:5601", transport=httpx.MockTransport(handler))
