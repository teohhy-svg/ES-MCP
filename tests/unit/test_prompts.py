from __future__ import annotations

from es_mcp_server.prompts.registry import (
    build_analyze_application_errors_prompt,
    build_investigate_incident_prompt,
    build_investigate_kibana_dashboard_prompt,
    build_optimize_search_query_prompt,
    build_troubleshoot_unassigned_shards_prompt,
)


def test_investigate_incident_prompt_guides_read_only_workflow() -> None:
    prompt = build_investigate_incident_prompt("red cluster", "last 15 minutes")

    assert "es_cluster_health" in prompt
    assert "es_nodes_summary" in prompt
    assert "Do not call write or destructive tools" in prompt


def test_unassigned_shards_prompt_uses_index_scope_when_provided() -> None:
    prompt = build_troubleshoot_unassigned_shards_prompt(index="logs-prod")

    assert "logs-prod" in prompt
    assert "es_shard_allocation" in prompt
    assert "read-only" in prompt


def test_analyze_application_errors_prompt_includes_service_and_time_range() -> None:
    prompt = build_analyze_application_errors_prompt(
        service="checkout",
        start_time="2026-01-01T00:00:00Z",
        end_time="2026-01-01T01:00:00Z",
        index="logs-*",
    )

    assert "checkout" in prompt
    assert "logs-*" in prompt
    assert "es_recent_logs" in prompt


def test_optimize_search_query_prompt_warns_against_risky_constructs() -> None:
    prompt = build_optimize_search_query_prompt(
        query_or_dsl='{"query": {"wildcard": {"message": "*error"}}}',
        index="logs-*",
        goal="reduce latency",
    )

    assert "leading wildcards" in prompt
    assert "es_index_mapping" in prompt
    assert "Do not execute the query" in prompt


def test_investigate_kibana_dashboard_prompt_uses_kibana_tools() -> None:
    prompt = build_investigate_kibana_dashboard_prompt(
        dashboard_id_or_title="Latency dashboard",
        symptoms="empty panels",
        space_id="observability",
    )

    assert "kbn_status" in prompt
    assert "kbn_dashboard_references" in prompt
    assert ".kibana*" in prompt
