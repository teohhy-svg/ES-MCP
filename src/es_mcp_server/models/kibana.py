"""Pydantic models for read-only Kibana MCP tools."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from es_mcp_server.models.common import StrictModel


class KibanaRequestTimeoutModel(StrictModel):
    request_timeout_seconds: float | None = Field(default=None, gt=0)


class KibanaStatusRequest(KibanaRequestTimeoutModel):
    pass


class KibanaSpacesRequest(KibanaRequestTimeoutModel):
    include_authorized_purposes: bool = False


class KibanaListDashboardsRequest(KibanaRequestTimeoutModel):
    search: str | None = Field(default=None, min_length=1)
    space_id: str | None = Field(default=None, min_length=1)
    size: int = Field(default=20, ge=1)
    page: int = Field(default=1, ge=1)


class KibanaDashboardRequest(KibanaRequestTimeoutModel):
    dashboard_id: str = Field(min_length=1)
    space_id: str | None = Field(default=None, min_length=1)


class KibanaDashboardReferencesRequest(KibanaDashboardRequest):
    pass


class KibanaStatusResponse(StrictModel):
    status: dict[str, Any]


class KibanaSpacesResponse(StrictModel):
    spaces: list[dict[str, Any]]


class KibanaDashboardSummary(StrictModel):
    id: str
    type: str = "dashboard"
    title: str | None = None
    description: str | None = None
    updated_at: str | None = None
    references: list[dict[str, Any]] = Field(default_factory=list)


class KibanaListDashboardsResponse(StrictModel):
    dashboards: list[KibanaDashboardSummary]
    total: int | None = None
    page: int
    per_page: int


class KibanaDashboardResponse(StrictModel):
    dashboard: dict[str, Any]


class KibanaDashboardReferencesResponse(StrictModel):
    dashboard_id: str
    title: str | None = None
    references: list[dict[str, Any]]
    panels: list[dict[str, Any]]
