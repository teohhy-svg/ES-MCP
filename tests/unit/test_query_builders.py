from __future__ import annotations

from datetime import datetime, timezone

from es_mcp_server.config import Settings
from es_mcp_server.es_client import (
    build_error_trends_body,
    build_recent_logs_body,
    build_safe_search_body,
)
from es_mcp_server.models.tools import ErrorTrendsRequest, RecentLogsRequest, SearchRequest


def test_build_safe_search_body_uses_simple_query_string_and_source_filter() -> None:
    settings = Settings(_env_file=None, elasticsearch_url="http://localhost:9200")
    request = SearchRequest(
        index="logs-prod",
        query="timeout",
        fields=["@timestamp", "message"],
        sort=["@timestamp:desc"],
    )

    body = build_safe_search_body(request, settings)

    assert body["query"]["bool"]["must"][0]["simple_query_string"]["query"] == "timeout"
    assert body["_source"] == ["@timestamp", "message"]
    assert body["sort"] == [{"@timestamp": {"order": "desc"}}]
    assert body["size"] == 10


def test_build_safe_search_body_caps_size() -> None:
    settings = Settings(
        _env_file=None,
        elasticsearch_url="http://localhost:9200",
        max_result_size=5,
    )
    request = SearchRequest(index="logs-prod", query="error", size=100)

    assert build_safe_search_body(request, settings)["size"] == 5


def test_build_recent_logs_body_adds_filters() -> None:
    request = RecentLogsRequest(
        start_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        end_time=datetime(2026, 1, 2, tzinfo=timezone.utc),
        service="checkout",
        severity="error",
        keyword="timeout",
    )

    body = build_recent_logs_body(request)
    filters = body["query"]["bool"]["filter"]

    assert {"term": {"service.name": "checkout"}} in filters
    assert {"term": {"log.level": "error"}} in filters
    assert body["query"]["bool"]["must"][0]["simple_query_string"]["query"] == "timeout"


def test_build_error_trends_body_groups_by_service() -> None:
    request = ErrorTrendsRequest(
        start_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        end_time=datetime(2026, 1, 2, tzinfo=timezone.utc),
        group_by="service",
    )

    body = build_error_trends_body(request)

    assert body["aggs"]["errors_over_time"]["date_histogram"]["fixed_interval"] == "5m"
    assert (
        body["aggs"]["errors_over_time"]["aggs"]["groups"]["terms"]["field"]
        == "service.name"
    )
