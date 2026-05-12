"""Elasticsearch client construction and read-only service methods."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from elasticsearch import Elasticsearch

from es_mcp_server.config import Settings
from es_mcp_server.models.responses import (
    ClusterHealthResponse,
    ErrorTrendBucket,
    ErrorTrendsResponse,
    IndexSummary,
    ListIndicesResponse,
    MappingResponse,
    NodeSummary,
    NodesSummaryResponse,
    RecentLogsResponse,
    SearchResponse,
    SettingsResponse,
    ShardAllocationResponse,
    SlowQueriesResponse,
    SnapshotStatusResponse,
)
from es_mcp_server.models.tools import (
    ClusterHealthRequest,
    DslSearchRequest,
    ErrorTrendsRequest,
    IndexMappingRequest,
    IndexSettingsRequest,
    ListIndicesRequest,
    NodesSummaryRequest,
    RecentLogsRequest,
    SearchRequest,
    ShardAllocationRequest,
    SlowQueriesRequest,
    SnapshotStatusRequest,
    TrendGroupBy,
)
from es_mcp_server.security import (
    cap_size,
    cap_timeout,
    mask_sensitive_value,
    validate_field_name,
    validate_field_names,
    validate_index_pattern,
    validate_limited_dsl,
    validate_repository_name,
    validate_sort,
)


def create_elasticsearch_client(settings: Settings) -> Elasticsearch:
    """Create the official Elasticsearch client from validated settings."""

    return Elasticsearch(
        settings.elasticsearch_url,
        **settings.elasticsearch_client_options(),
    )


class ElasticsearchService:
    """Read-only Elasticsearch operations used by MCP tool handlers."""

    def __init__(self, client: Elasticsearch, settings: Settings) -> None:
        self.client = client
        self.settings = settings

    def cluster_health(self, request: ClusterHealthRequest) -> dict[str, Any]:
        timeout = cap_timeout(request.request_timeout_seconds, self.settings)
        response = self._client(timeout).cluster.health(level=request.level.value)
        return ClusterHealthResponse(
            cluster_name=response.get("cluster_name"),
            status=response.get("status", "unknown"),
            number_of_nodes=_int(response.get("number_of_nodes")),
            number_of_data_nodes=_int(response.get("number_of_data_nodes")),
            active_primary_shards=_int(response.get("active_primary_shards")),
            active_shards=_int(response.get("active_shards")),
            relocating_shards=_int(response.get("relocating_shards")),
            initializing_shards=_int(response.get("initializing_shards")),
            unassigned_shards=_int(response.get("unassigned_shards")),
            timed_out=bool(response.get("timed_out", False)),
        ).model_dump(mode="json")

    def nodes_summary(self, request: NodesSummaryRequest) -> dict[str, Any]:
        timeout = cap_timeout(request.request_timeout_seconds, self.settings)
        metrics = ["jvm", "os", "fs", "process"]
        if request.include_indices:
            metrics.append("indices")
        response = self._client(timeout).nodes.stats(metric=metrics)
        nodes = []
        for node_id, node in response.get("nodes", {}).items():
            fs_total = node.get("fs", {}).get("total", {})
            nodes.append(
                NodeSummary(
                    node_id=node_id,
                    name=node.get("name"),
                    host=node.get("host"),
                    roles=list(node.get("roles", [])),
                    jvm_heap_used_percent=_optional_int(
                        node.get("jvm", {}).get("mem", {}).get("heap_used_percent")
                    ),
                    cpu_percent=_first_int(
                        node.get("os", {}).get("cpu", {}).get("percent"),
                        node.get("process", {}).get("cpu", {}).get("percent"),
                    ),
                    disk_available_bytes=_optional_int(fs_total.get("available_in_bytes")),
                    disk_total_bytes=_optional_int(fs_total.get("total_in_bytes")),
                )
            )
        return NodesSummaryResponse(nodes=nodes).model_dump(mode="json")

    def list_indices(self, request: ListIndicesRequest) -> dict[str, Any]:
        timeout = cap_timeout(request.request_timeout_seconds, self.settings)
        pattern = validate_index_pattern(
            request.pattern,
            self.settings,
            include_hidden=request.include_hidden,
        )
        size = cap_size(request.size, self.settings)
        expand_wildcards = "all" if request.include_hidden else "open"
        rows = self._client(timeout).cat.indices(
            index=pattern,
            format="json",
            h="health,status,index,docs.count,store.size",
            expand_wildcards=expand_wildcards,
        )
        creation_dates = self._index_creation_dates(pattern, timeout, expand_wildcards)
        summaries = [
            IndexSummary(
                name=str(row.get("index", "")),
                health=row.get("health"),
                status=row.get("status"),
                docs_count=_optional_int(row.get("docs.count")),
                store_size=row.get("store.size"),
                creation_date=creation_dates.get(str(row.get("index", ""))),
            )
            for row in rows[:size]
        ]
        return ListIndicesResponse(
            indices=summaries,
            truncated=len(rows) > size,
        ).model_dump(mode="json")

    def index_mapping(self, request: IndexMappingRequest) -> dict[str, Any]:
        timeout = cap_timeout(request.request_timeout_seconds, self.settings)
        index = validate_index_pattern(request.index, self.settings)
        mapping = self._client(timeout).indices.get_mapping(index=index)
        return MappingResponse(index=index, mapping=dict(mapping)).model_dump(mode="json")

    def index_settings(self, request: IndexSettingsRequest) -> dict[str, Any]:
        timeout = cap_timeout(request.request_timeout_seconds, self.settings)
        index = validate_index_pattern(request.index, self.settings)
        settings = self._client(timeout).indices.get_settings(
            index=index,
            include_defaults=request.include_defaults,
        )
        return SettingsResponse(
            index=index,
            settings=mask_sensitive_value(dict(settings)),
        ).model_dump(mode="json")

    def search(self, request: SearchRequest) -> dict[str, Any]:
        timeout = cap_timeout(request.request_timeout_seconds, self.settings)
        index = validate_index_pattern(request.index, self.settings)
        body = build_safe_search_body(request, self.settings)
        size = cap_size(request.size, self.settings)
        response = self._client(timeout).search(index=index, body=body, size=size)
        return _search_response(index, response).model_dump(mode="json")

    def dsl_search(self, request: DslSearchRequest) -> dict[str, Any]:
        timeout = cap_timeout(request.request_timeout_seconds, self.settings)
        index = validate_index_pattern(request.index, self.settings)
        body = validate_limited_dsl(request.dsl)
        body["track_total_hits"] = body.get("track_total_hits", True)
        size = cap_size(request.size, self.settings)
        response = self._client(timeout).search(index=index, body=body, size=size)
        return _search_response(index, response).model_dump(mode="json")

    def recent_logs(self, request: RecentLogsRequest) -> dict[str, Any]:
        timeout = cap_timeout(request.request_timeout_seconds, self.settings)
        index = validate_index_pattern(
            request.index or self.settings.log_index_pattern,
            self.settings,
        )
        body = build_recent_logs_body(request)
        size = cap_size(request.size, self.settings)
        response = self._client(timeout).search(index=index, body=body, size=size)
        search = _search_response(index, response)
        return RecentLogsResponse(
            index=index,
            took_ms=search.took_ms,
            hits=search.hits,
        ).model_dump(mode="json")

    def error_trends(self, request: ErrorTrendsRequest) -> dict[str, Any]:
        timeout = cap_timeout(request.request_timeout_seconds, self.settings)
        index = validate_index_pattern(
            request.index or self.settings.log_index_pattern,
            self.settings,
        )
        body = build_error_trends_body(request)
        response = self._client(timeout).search(index=index, body=body, size=0)
        buckets = _trend_buckets(response)
        return ErrorTrendsResponse(buckets=buckets).model_dump(mode="json")

    def slow_queries(self, request: SlowQueriesRequest) -> dict[str, Any]:
        configured_index = request.index or self.settings.slow_log_index_pattern
        if not configured_index:
            return SlowQueriesResponse(configured=False, hits=[]).model_dump(mode="json")

        timeout = cap_timeout(request.request_timeout_seconds, self.settings)
        index = validate_index_pattern(configured_index, self.settings)
        body = build_slow_queries_body(request)
        size = cap_size(request.size, self.settings)
        response = self._client(timeout).search(index=index, body=body, size=size)
        return SlowQueriesResponse(
            configured=True,
            hits=_hits(response),
        ).model_dump(mode="json")

    def shard_allocation(self, request: ShardAllocationRequest) -> dict[str, Any]:
        timeout = cap_timeout(request.request_timeout_seconds, self.settings)
        index = None
        if request.index:
            index = validate_index_pattern(request.index, self.settings)
        shard_kwargs: dict[str, Any] = {"format": "json"}
        if index:
            shard_kwargs["index"] = index
        cat = self._client(timeout).cat.shards(**shard_kwargs)
        explanations: list[dict[str, Any]] = []
        if request.include_explanations:
            explanations = self._unassigned_explanations(cat, timeout)
        return ShardAllocationResponse(
            shards=[dict(row) for row in cat],
            unassigned_explanations=explanations,
        ).model_dump(mode="json")

    def snapshot_status(self, request: SnapshotStatusRequest) -> dict[str, Any]:
        timeout = cap_timeout(request.request_timeout_seconds, self.settings)
        repository = validate_repository_name(request.repository) if request.repository else None
        size = cap_size(request.size, self.settings)
        permission_limited = False
        repositories: list[dict[str, Any]] = []
        snapshots: list[dict[str, Any]] = []

        try:
            repo_response = self._client(timeout).snapshot.get_repository(
                name=repository or "*"
            )
            repositories = [
                {"name": name, **dict(details)} for name, details in dict(repo_response).items()
            ]
        except Exception as exc:  # pragma: no cover - depends on cluster privileges
            permission_limited = True
            repositories = [{"error": _safe_exception_message(exc)}]

        if request.include_snapshots and not permission_limited:
            for repo in repositories[:size]:
                repo_name = str(repo.get("name"))
                try:
                    snapshot_response = self._client(timeout).snapshot.get(
                        repository=repo_name,
                        snapshot="_all",
                        size=size,
                    )
                    for snapshot in snapshot_response.get("snapshots", [])[:size]:
                        snapshots.append({"repository": repo_name, **dict(snapshot)})
                except Exception as exc:  # pragma: no cover - depends on cluster privileges
                    permission_limited = True
                    snapshots.append(
                        {"repository": repo_name, "error": _safe_exception_message(exc)}
                    )
                    break

        return SnapshotStatusResponse(
            repositories=repositories[:size],
            snapshots=snapshots[:size],
            permission_limited=permission_limited,
        ).model_dump(mode="json")

    def _client(self, timeout: float) -> Elasticsearch:
        return self.client.options(request_timeout=timeout)

    def _index_creation_dates(
        self,
        pattern: str,
        timeout: float,
        expand_wildcards: str,
    ) -> dict[str, str]:
        try:
            response = self._client(timeout).indices.get_settings(
                index=pattern,
                name="index.creation_date",
                flat_settings=True,
                expand_wildcards=expand_wildcards,
            )
        except Exception:
            return {}
        creation_dates = {}
        for index, details in dict(response).items():
            settings = details.get("settings", {})
            value = settings.get("index.creation_date") or settings.get("index", {}).get(
                "creation_date"
            )
            if value:
                creation_dates[index] = str(value)
        return creation_dates

    def _unassigned_explanations(
        self,
        shards: list[dict[str, Any]],
        timeout: float,
    ) -> list[dict[str, Any]]:
        explanations = []
        for shard in shards:
            if str(shard.get("state", "")).upper() != "UNASSIGNED":
                continue
            if len(explanations) >= 10:
                break
            try:
                body = {
                    "index": shard.get("index"),
                    "shard": _int(shard.get("shard")),
                    "primary": str(shard.get("prirep", "")).lower().startswith("p"),
                }
                explanations.append(
                    dict(self._client(timeout).cluster.allocation_explain(body=body))
                )
            except Exception as exc:  # pragma: no cover - depends on cluster privileges/state
                explanations.append(
                    {
                        "index": shard.get("index"),
                        "shard": shard.get("shard"),
                        "permission_limited": True,
                        "error": _safe_exception_message(exc),
                    }
                )
        return explanations


def build_safe_search_body(request: SearchRequest, settings: Settings) -> dict[str, Any]:
    must: list[dict[str, Any]] = []
    filters: list[dict[str, Any]] = []
    fields = validate_field_names(request.fields)

    if request.query:
        must.append(
            {
                "simple_query_string": {
                    "query": request.query,
                    "fields": fields or ["*"],
                    "default_operator": "and",
                }
            }
        )
    if request.match:
        for field, value in request.match.items():
            must.append({"match": {validate_field_name(field): value}})
    if request.timestamp_field:
        filters.append(_time_range(request.timestamp_field, request.start_time, request.end_time))

    body: dict[str, Any] = {
        "query": {"bool": {"must": must or [{"match_all": {}}], "filter": filters}},
        "track_total_hits": True,
    }
    if fields:
        body["_source"] = fields

    sort = validate_sort(request.sort)
    if sort:
        body["sort"] = [_sort_entry(item) for item in sort]

    body["size"] = cap_size(request.size, settings)
    return body


def build_recent_logs_body(request: RecentLogsRequest) -> dict[str, Any]:
    filters = [_time_range(request.timestamp_field, request.start_time, request.end_time)]
    if request.service:
        filters.append({"term": {validate_field_name(request.service_field): request.service}})
    if request.severity:
        filters.append({"term": {validate_field_name(request.severity_field): request.severity}})

    must = []
    if request.keyword:
        must.append({"simple_query_string": {"query": request.keyword, "default_operator": "and"}})

    return {
        "query": {"bool": {"filter": filters, "must": must}},
        "sort": [{validate_field_name(request.timestamp_field): {"order": "desc"}}],
        "track_total_hits": True,
    }


def build_error_trends_body(request: ErrorTrendsRequest) -> dict[str, Any]:
    group_field = {
        TrendGroupBy.SERVICE: request.service_field,
        TrendGroupBy.INDEX: "_index",
        TrendGroupBy.SEVERITY: request.severity_field,
    }[request.group_by]
    return {
        "query": {
            "bool": {
                "filter": [
                    _time_range(request.timestamp_field, request.start_time, request.end_time),
                    {"terms": {validate_field_name(request.severity_field): request.error_levels}},
                ]
            }
        },
        "aggs": {
            "errors_over_time": {
                "date_histogram": {
                    "field": validate_field_name(request.timestamp_field),
                    "fixed_interval": request.interval,
                    "min_doc_count": 0,
                },
                "aggs": {
                    "groups": {
                        "terms": {
                            "field": validate_field_name(group_field),
                            "size": 20,
                        }
                    }
                },
            }
        },
        "track_total_hits": False,
    }


def build_slow_queries_body(request: SlowQueriesRequest) -> dict[str, Any]:
    filters = [_time_range(request.timestamp_field, request.start_time, request.end_time)]
    if request.threshold_ms is not None:
        filters.append(
            {"range": {"elasticsearch.slowlog.took_millis": {"gte": request.threshold_ms}}}
        )
    return {
        "query": {"bool": {"filter": filters}},
        "sort": [{validate_field_name(request.timestamp_field): {"order": "desc"}}],
        "track_total_hits": True,
    }


def _time_range(
    field: str,
    start_time: datetime | None,
    end_time: datetime | None,
) -> dict[str, Any]:
    range_body: dict[str, str] = {}
    if start_time is not None:
        range_body["gte"] = start_time.isoformat()
    if end_time is not None:
        range_body["lt"] = end_time.isoformat()
    return {"range": {validate_field_name(field): range_body}}


def _sort_entry(item: str) -> dict[str, Any]:
    if ":" not in item:
        return {item: {"order": "asc"}}
    field, order = item.rsplit(":", 1)
    return {field: {"order": order}}


def _search_response(index: str, response: dict[str, Any]) -> SearchResponse:
    return SearchResponse(
        index=index,
        took_ms=_int(response.get("took")),
        timed_out=bool(response.get("timed_out", False)),
        total=_total(response),
        hits=_hits(response),
        aggregations=response.get("aggregations"),
    )


def _hits(response: dict[str, Any]) -> list[dict[str, Any]]:
    return [dict(hit) for hit in response.get("hits", {}).get("hits", [])]


def _total(response: dict[str, Any]) -> int | str | None:
    total = response.get("hits", {}).get("total")
    if isinstance(total, Mapping):
        value = total.get("value")
        relation = total.get("relation")
        return f">={value}" if relation and relation != "eq" else _optional_int(value)
    return _optional_int(total)


def _trend_buckets(response: dict[str, Any]) -> list[ErrorTrendBucket]:
    buckets = []
    raw_buckets = (
        response.get("aggregations", {})
        .get("errors_over_time", {})
        .get("buckets", [])
    )
    for bucket in raw_buckets:
        groups = {
            str(group.get("key")): _int(group.get("doc_count"))
            for group in bucket.get("groups", {}).get("buckets", [])
        }
        buckets.append(
            ErrorTrendBucket(timestamp=str(bucket.get("key_as_string")), groups=groups)
        )
    return buckets


def _int(value: Any) -> int:
    return _optional_int(value) or 0


def _optional_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _first_int(*values: Any) -> int | None:
    for value in values:
        parsed = _optional_int(value)
        if parsed is not None:
            return parsed
    return None


def _safe_exception_message(exc: Exception) -> str:
    return str(mask_sensitive_value(str(exc)))
