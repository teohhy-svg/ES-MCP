"""Pydantic models for read-only Kibana MCP tools."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

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


class KibanaSpaceRequest(KibanaRequestTimeoutModel):
    space_id: str | None = Field(default=None, min_length=1)


class KibanaPagedRequest(KibanaSpaceRequest):
    size: int = Field(default=20, ge=1)
    page: int = Field(default=1, ge=1)


class KibanaObjectRequest(KibanaSpaceRequest):
    object_id: str = Field(min_length=1)


class KibanaListRulesRequest(KibanaPagedRequest):
    search: str | None = Field(default=None, min_length=1)


class KibanaRuleRequest(KibanaObjectRequest):
    pass


class KibanaRuleQueryRequest(KibanaRuleRequest):
    mode: Literal["build"] = "build"
    alert_id: str | None = Field(default=None, min_length=1)


class KibanaCaseOwner(StrEnum):
    CASES = "cases"
    OBSERVABILITY = "observability"
    SECURITY = "securitySolution"


class KibanaCaseStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in-progress"
    CLOSED = "closed"


class KibanaCaseSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class KibanaListCasesRequest(KibanaPagedRequest):
    search: str | None = Field(default=None, min_length=1)
    owner: KibanaCaseOwner | None = None
    status: KibanaCaseStatus | None = None
    severity: KibanaCaseSeverity | None = None
    tags: list[str] = Field(default_factory=list, max_length=50)


class KibanaCaseRequest(KibanaObjectRequest):
    pass


class KibanaCaseActivityRequest(KibanaCaseRequest):
    size: int = Field(default=20, ge=1)
    page: int = Field(default=1, ge=1)
    sort_order: Literal["asc", "desc"] = "desc"


class KibanaWorkflowManaged(StrEnum):
    ALL = "all"
    MANAGED = "managed"
    UNMANAGED = "unmanaged"


class KibanaListWorkflowsRequest(KibanaPagedRequest):
    query: str | None = Field(default=None, min_length=1)
    enabled: bool | None = None
    tags: list[str] = Field(default_factory=list, max_length=50)
    managed: KibanaWorkflowManaged = KibanaWorkflowManaged.ALL


class KibanaWorkflowRequest(KibanaObjectRequest):
    pass


class KibanaWorkflowExecutionStatus(StrEnum):
    PENDING = "pending"
    WAITING = "waiting"
    WAITING_FOR_INPUT = "waiting_for_input"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"
    SKIPPED = "skipped"


class KibanaWorkflowExecutionsRequest(KibanaWorkflowRequest):
    size: int = Field(default=20, ge=1)
    page: int = Field(default=1, ge=1)
    status: KibanaWorkflowExecutionStatus | None = None
    omit_step_runs: bool = True


class KibanaAgentRequest(KibanaObjectRequest):
    pass


class KibanaFleetAgentsRequest(KibanaPagedRequest):
    kuery: str | None = Field(default=None, min_length=1)
    show_inactive: bool = False
    with_metrics: bool = False
    get_status_summary: bool = True


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
