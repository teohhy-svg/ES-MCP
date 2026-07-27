"""Read-only Kibana MCP tools."""

from __future__ import annotations

from typing import Any, Literal

from mcp.server.fastmcp import FastMCP

from es_mcp_server.config import Settings
from es_mcp_server.kibana_client import KibanaService
from es_mcp_server.models.kibana import (
    KibanaAgentRequest,
    KibanaCaseActivityRequest,
    KibanaCaseRequest,
    KibanaDashboardReferencesRequest,
    KibanaDashboardRequest,
    KibanaFleetAgentsRequest,
    KibanaListCasesRequest,
    KibanaListDashboardsRequest,
    KibanaListRulesRequest,
    KibanaListWorkflowsRequest,
    KibanaRuleQueryRequest,
    KibanaRuleRequest,
    KibanaSpaceRequest,
    KibanaSpacesRequest,
    KibanaStatusRequest,
    KibanaWorkflowExecutionsRequest,
    KibanaWorkflowRequest,
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

    @mcp.tool()
    def kbn_capability_report(
        space_id: str | None = None,
        request_timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        """Probe read access to major Kibana operational feature APIs."""

        return _run_kibana(
            settings,
            "kbn_capability_report",
            space_id,
            lambda: service.capability_report(
                KibanaSpaceRequest(
                    space_id=space_id,
                    request_timeout_seconds=request_timeout_seconds,
                )
            ),
        )

    @mcp.tool()
    def kbn_alerting_health(
        space_id: str | None = None,
        request_timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        """Return alerting framework execution, decryption, and read health."""

        return _run_kibana(
            settings,
            "kbn_alerting_health",
            space_id,
            lambda: service.alerting_health(
                KibanaSpaceRequest(
                    space_id=space_id,
                    request_timeout_seconds=request_timeout_seconds,
                )
            ),
        )

    @mcp.tool()
    def kbn_rule_types(
        space_id: str | None = None,
        request_timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        """List rule types visible to the configured Kibana principal."""

        return _run_kibana(
            settings,
            "kbn_rule_types",
            space_id,
            lambda: service.rule_types(
                KibanaSpaceRequest(
                    space_id=space_id,
                    request_timeout_seconds=request_timeout_seconds,
                )
            ),
        )

    @mcp.tool()
    def kbn_list_rules(
        search: str | None = None,
        space_id: str | None = None,
        size: int = 20,
        page: int = 1,
        request_timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        """Search alerting rules in a Kibana space."""

        return _run_kibana(
            settings,
            "kbn_list_rules",
            space_id,
            lambda: service.list_rules(
                KibanaListRulesRequest(
                    search=search,
                    space_id=space_id,
                    size=size,
                    page=page,
                    request_timeout_seconds=request_timeout_seconds,
                )
            ),
        )

    @mcp.tool()
    def kbn_get_rule(
        rule_id: str,
        space_id: str | None = None,
        request_timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        """Get a rule, including schedule, actions, and execution status."""

        return _run_kibana(
            settings,
            "kbn_get_rule",
            space_id,
            lambda: service.get_rule(
                KibanaRuleRequest(
                    object_id=rule_id,
                    space_id=space_id,
                    request_timeout_seconds=request_timeout_seconds,
                )
            ),
        )

    @mcp.tool()
    def kbn_rule_query(
        rule_id: str,
        alert_id: str | None = None,
        space_id: str | None = None,
        request_timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        """Build, but do not execute, the Elasticsearch query for a supported rule."""

        return _run_kibana(
            settings,
            "kbn_rule_query",
            space_id,
            lambda: service.rule_query(
                KibanaRuleQueryRequest(
                    object_id=rule_id,
                    alert_id=alert_id,
                    space_id=space_id,
                    request_timeout_seconds=request_timeout_seconds,
                )
            ),
        )

    @mcp.tool()
    def kbn_list_connectors(
        space_id: str | None = None,
        request_timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        """List configured action connectors without connector secrets."""

        return _run_kibana(
            settings,
            "kbn_list_connectors",
            space_id,
            lambda: service.connectors(
                KibanaSpaceRequest(
                    space_id=space_id,
                    request_timeout_seconds=request_timeout_seconds,
                )
            ),
        )

    @mcp.tool()
    def kbn_list_cases(
        search: str | None = None,
        owner: Literal["cases", "observability", "securitySolution"] | None = None,
        status: Literal["open", "in-progress", "closed"] | None = None,
        severity: Literal["low", "medium", "high", "critical"] | None = None,
        tags: list[str] | None = None,
        space_id: str | None = None,
        size: int = 20,
        page: int = 1,
        request_timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        """Search cases by owner, status, severity, tags, or title."""

        return _run_kibana(
            settings,
            "kbn_list_cases",
            space_id,
            lambda: service.list_cases(
                KibanaListCasesRequest(
                    search=search,
                    owner=owner,
                    status=status,
                    severity=severity,
                    tags=tags or [],
                    space_id=space_id,
                    size=size,
                    page=page,
                    request_timeout_seconds=request_timeout_seconds,
                )
            ),
        )

    @mcp.tool()
    def kbn_get_case(
        case_id: str,
        space_id: str | None = None,
        request_timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        """Get case metadata and alert totals without mutating the case."""

        return _run_kibana(
            settings,
            "kbn_get_case",
            space_id,
            lambda: service.get_case(
                KibanaCaseRequest(
                    object_id=case_id,
                    space_id=space_id,
                    request_timeout_seconds=request_timeout_seconds,
                )
            ),
        )

    @mcp.tool()
    def kbn_case_alerts(
        case_id: str,
        space_id: str | None = None,
        request_timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        """List alerts currently attached to a case."""

        return _run_kibana(
            settings,
            "kbn_case_alerts",
            space_id,
            lambda: service.case_alerts(
                KibanaCaseRequest(
                    object_id=case_id,
                    space_id=space_id,
                    request_timeout_seconds=request_timeout_seconds,
                )
            ),
        )

    @mcp.tool()
    def kbn_case_activity(
        case_id: str,
        space_id: str | None = None,
        size: int = 20,
        page: int = 1,
        sort_order: Literal["asc", "desc"] = "desc",
        request_timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        """List the audit-style activity history for a case."""

        return _run_kibana(
            settings,
            "kbn_case_activity",
            space_id,
            lambda: service.case_activity(
                KibanaCaseActivityRequest(
                    object_id=case_id,
                    space_id=space_id,
                    size=size,
                    page=page,
                    sort_order=sort_order,
                    request_timeout_seconds=request_timeout_seconds,
                )
            ),
        )

    @mcp.tool()
    def kbn_list_workflows(
        query: str | None = None,
        enabled: bool | None = None,
        tags: list[str] | None = None,
        managed: Literal["all", "managed", "unmanaged"] = "all",
        space_id: str | None = None,
        size: int = 20,
        page: int = 1,
        request_timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        """List Kibana workflows when the target version supports Workflows APIs."""

        return _run_kibana(
            settings,
            "kbn_list_workflows",
            space_id,
            lambda: service.list_workflows(
                KibanaListWorkflowsRequest(
                    query=query,
                    enabled=enabled,
                    tags=tags or [],
                    managed=managed,
                    space_id=space_id,
                    size=size,
                    page=page,
                    request_timeout_seconds=request_timeout_seconds,
                )
            ),
        )

    @mcp.tool()
    def kbn_get_workflow(
        workflow_id: str,
        space_id: str | None = None,
        request_timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        """Get a workflow definition and validation state."""

        return _run_kibana(
            settings,
            "kbn_get_workflow",
            space_id,
            lambda: service.get_workflow(
                KibanaWorkflowRequest(
                    object_id=workflow_id,
                    space_id=space_id,
                    request_timeout_seconds=request_timeout_seconds,
                )
            ),
        )

    @mcp.tool()
    def kbn_workflow_executions(
        workflow_id: str,
        status: Literal[
            "pending",
            "waiting",
            "waiting_for_input",
            "running",
            "completed",
            "failed",
            "cancelled",
            "timed_out",
            "skipped",
        ]
        | None = None,
        omit_step_runs: bool = True,
        space_id: str | None = None,
        size: int = 20,
        page: int = 1,
        request_timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        """List recent executions for a workflow."""

        return _run_kibana(
            settings,
            "kbn_workflow_executions",
            space_id,
            lambda: service.workflow_executions(
                KibanaWorkflowExecutionsRequest(
                    object_id=workflow_id,
                    status=status,
                    omit_step_runs=omit_step_runs,
                    space_id=space_id,
                    size=size,
                    page=page,
                    request_timeout_seconds=request_timeout_seconds,
                )
            ),
        )

    @mcp.tool()
    def kbn_workflow_connectors(
        space_id: str | None = None,
        request_timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        """List connectors and step capabilities available to workflows."""

        return _run_kibana(
            settings,
            "kbn_workflow_connectors",
            space_id,
            lambda: service.workflow_connectors(
                KibanaSpaceRequest(
                    space_id=space_id,
                    request_timeout_seconds=request_timeout_seconds,
                )
            ),
        )

    @mcp.tool()
    def kbn_list_ai_agents(
        space_id: str | None = None,
        request_timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        """List Elastic Agent Builder agents visible to the principal."""

        return _run_kibana(
            settings,
            "kbn_list_ai_agents",
            space_id,
            lambda: service.ai_agents(
                KibanaSpaceRequest(
                    space_id=space_id,
                    request_timeout_seconds=request_timeout_seconds,
                )
            ),
        )

    @mcp.tool()
    def kbn_get_ai_agent(
        agent_id: str,
        space_id: str | None = None,
        request_timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        """Get an Elastic Agent Builder agent configuration."""

        return _run_kibana(
            settings,
            "kbn_get_ai_agent",
            space_id,
            lambda: service.get_ai_agent(
                KibanaAgentRequest(
                    object_id=agent_id,
                    space_id=space_id,
                    request_timeout_seconds=request_timeout_seconds,
                )
            ),
        )

    @mcp.tool()
    def kbn_list_ai_tools(
        space_id: str | None = None,
        request_timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        """List tools available to Elastic Agent Builder agents."""

        return _run_kibana(
            settings,
            "kbn_list_ai_tools",
            space_id,
            lambda: service.ai_tools(
                KibanaSpaceRequest(
                    space_id=space_id,
                    request_timeout_seconds=request_timeout_seconds,
                )
            ),
        )

    @mcp.tool()
    def kbn_list_fleet_agents(
        kuery: str | None = None,
        show_inactive: bool = False,
        with_metrics: bool = False,
        get_status_summary: bool = True,
        space_id: str | None = None,
        size: int = 20,
        page: int = 1,
        request_timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        """List Elastic Fleet agents and optional health metrics."""

        return _run_kibana(
            settings,
            "kbn_list_fleet_agents",
            space_id,
            lambda: service.fleet_agents(
                KibanaFleetAgentsRequest(
                    kuery=kuery,
                    show_inactive=show_inactive,
                    with_metrics=with_metrics,
                    get_status_summary=get_status_summary,
                    space_id=space_id,
                    size=size,
                    page=page,
                    request_timeout_seconds=request_timeout_seconds,
                )
            ),
        )


def _run_kibana(
    settings: Settings,
    tool_name: str,
    space_id: str | None,
    action: Any,
) -> dict[str, Any]:
    return run_tool(
        settings=settings,
        tool_name=tool_name,
        operation_type="kibana_read",
        index_or_pattern=space_id or settings.kibana_space_id,
        action=action,
    )
