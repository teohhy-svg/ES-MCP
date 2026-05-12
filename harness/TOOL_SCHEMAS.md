# MCP Tool Schema Proposal

## Shared Conventions
- All input models are Pydantic models with strict validation.
- All tools accept an optional `request_timeout_seconds` where useful, capped by `ES_MAX_TIMEOUT_SECONDS`.
- All tools return structured dictionaries that are safe for MCP clients to display.
- Index parameters are validated by `security.py` before Elasticsearch calls.
- Errors are sanitized and include a stable `error_type`, `message`, and optional `request_id`.

## 1. `es_cluster_health`
Mission: Return high-level cluster health.

Input:
```text
level: "cluster" | "indices" | "shards" = "cluster"
request_timeout_seconds: float | None
```

Output:
```text
cluster_name: str
status: "green" | "yellow" | "red" | "unknown"
number_of_nodes: int
number_of_data_nodes: int
active_primary_shards: int
active_shards: int
relocating_shards: int
initializing_shards: int
unassigned_shards: int
timed_out: bool
```

Guards:
- Read-only.
- Timeout capped.

## 2. `es_nodes_summary`
Mission: Return basic node information, JVM memory, CPU, disk, and roles.

Input:
```text
include_indices: bool = false
request_timeout_seconds: float | None
```

Output:
```text
nodes: list[{
  node_id: str
  name: str
  host: str | None
  roles: list[str]
  jvm_heap_used_percent: int | None
  cpu_percent: int | None
  disk_available_bytes: int | None
  disk_total_bytes: int | None
}]
```

Guards:
- Read-only.
- Returns summarized fields only.

## 3. `es_list_indices`
Mission: List indices with health, status, document count, store size, and creation date when available.

Input:
```text
pattern: str = "*"
include_hidden: bool = false
size: int = 100
request_timeout_seconds: float | None
```

Output:
```text
indices: list[{
  name: str
  health: str | None
  status: str | None
  docs_count: int | None
  store_size: str | None
  creation_date: str | None
}]
truncated: bool
```

Guards:
- Pattern must pass allowlist and denylist checks.
- `size` capped by `ES_MAX_RESULT_SIZE`.
- Hidden/system indices excluded unless allowed by configuration and requested.

## 4. `es_index_mapping`
Mission: Show mapping for a specific index or allowed pattern.

Input:
```text
index: str
request_timeout_seconds: float | None
```

Output:
```text
index: str
mapping: dict
```

Guards:
- Index must pass allowlist and denylist checks.
- Response may be truncated in future if mappings are very large.

## 5. `es_index_settings`
Mission: Show settings for a specific index or allowed pattern.

Input:
```text
index: str
include_defaults: bool = false
request_timeout_seconds: float | None
```

Output:
```text
index: str
settings: dict
```

Guards:
- Index must pass allowlist and denylist checks.
- Sensitive setting values are masked before return.

## 6. `es_search`
Mission: Search an index using safe high-level parameters.

Input:
```text
index: str
query: str | None
match: dict[str, str | int | float | bool] | None
fields: list[str] | None
size: int = 10
sort: list[str] | None
timestamp_field: str | None
start_time: datetime | None
end_time: datetime | None
request_timeout_seconds: float | None
```

Output:
```text
index: str
took_ms: int
timed_out: bool
total: int | str | None
hits: list[dict]
```

Guards:
- Requires either `query`, `match`, or a time range.
- Builds safe `simple_query_string`, `match`, and `range` clauses.
- `fields` are used for `_source` filtering.
- `size` capped by `ES_MAX_RESULT_SIZE`.
- Sort fields are validated as simple field names with optional `:asc` or `:desc`.

## 7. `es_dsl_search`
Mission: Accept limited Elasticsearch DSL with validation.

Input:
```text
index: str
dsl: dict
size: int = 10
request_timeout_seconds: float | None
```

Allowed DSL clauses:
```text
query.bool
query.match
query.multi_match
query.term
query.terms
query.range
query.exists
query.ids
query.prefix
query.simple_query_string
sort
aggs.date_histogram
aggs.terms
_source
track_total_hits
```

Blocked constructs:
```text
script
script_score
function_score
runtime_mappings
regexp
percolate
more_like_this
wildcard with leading wildcard or very short pattern
query_string
knn
collapse
suggest
profile
explain
from beyond configured limit
```

Output:
```text
index: str
took_ms: int
timed_out: bool
total: int | str | None
hits: list[dict]
aggregations: dict | None
```

Guards:
- Deep recursive DSL validation.
- Enforces size and timeout regardless of supplied DSL.
- Blocks expensive wildcard abuse and dangerous constructs.

## 8. `es_recent_logs`
Mission: Query log indices by timestamp range, service, severity, and keyword.

Input:
```text
index: str | None
timestamp_field: str = "@timestamp"
start_time: datetime
end_time: datetime
service_field: str = "service.name"
service: str | None
severity_field: str = "log.level"
severity: str | None
keyword: str | None
size: int = 50
request_timeout_seconds: float | None
```

Output:
```text
index: str
took_ms: int
hits: list[dict]
```

Guards:
- Defaults to `ES_LOG_INDEX_PATTERN`.
- Requires bounded time range.
- Size capped.

## 9. `es_error_trends`
Mission: Aggregate error counts over time by service, index, or severity.

Input:
```text
index: str | None
timestamp_field: str = "@timestamp"
start_time: datetime
end_time: datetime
interval: str = "5m"
group_by: "service" | "index" | "severity" = "service"
service_field: str = "service.name"
severity_field: str = "log.level"
error_levels: list[str] = ["error", "fatal", "critical"]
request_timeout_seconds: float | None
```

Output:
```text
buckets: list[{
  timestamp: str
  groups: dict[str, int]
}]
```

Guards:
- Defaults to `ES_LOG_INDEX_PATTERN`.
- Requires bounded time range.
- Aggregation bucket count capped.

## 10. `es_slow_queries`
Mission: Search slow logs when a slow-log index pattern is configured.

Input:
```text
index: str | None
timestamp_field: str = "@timestamp"
start_time: datetime
end_time: datetime
threshold_ms: int | None
size: int = 50
request_timeout_seconds: float | None
```

Output:
```text
configured: bool
hits: list[dict]
```

Guards:
- Requires `ES_SLOW_LOG_INDEX_PATTERN` if `index` is omitted.
- Requires bounded time range.

## 11. `es_shard_allocation`
Mission: Return shard allocation and unassigned shard explanation when available.

Input:
```text
index: str | None
include_explanations: bool = true
request_timeout_seconds: float | None
```

Output:
```text
shards: list[dict]
unassigned_explanations: list[dict]
```

Guards:
- Index filter must pass policy if provided.
- Explanation failures due to permissions are returned as sanitized partial results.

## 12. `es_snapshot_status`
Mission: Show snapshot repositories and recent snapshot status when permissions allow.

Input:
```text
repository: str | None
include_snapshots: bool = true
size: int = 20
request_timeout_seconds: float | None
```

Output:
```text
repositories: list[dict]
snapshots: list[dict]
permission_limited: bool
```

Guards:
- Read-only.
- Permission failures are sanitized and marked as permission-limited.

## 13. `es_create_index`
Mission: Create an index when write tools are explicitly enabled.

Input:
```text
index: str
settings: dict | None
mappings: dict | None
confirm: bool
request_timeout_seconds: float | None
```

Output:
```text
acknowledged: bool
index: str
```

Guards:
- Requires `ES_ENABLE_WRITE_TOOLS=true`.
- Requires `confirm=true`.
- Index must be exact, valid, and allowed.
- Settings and mappings are validated for dangerous constructs.

## 14. `es_delete_index`
Mission: Delete an exact index when destructive tools are explicitly enabled.

Input:
```text
index: str
confirmation_phrase: str
request_timeout_seconds: float | None
```

Output:
```text
acknowledged: bool
index: str
```

Guards:
- Requires `ES_ENABLE_DESTRUCTIVE_TOOLS=true`.
- Requires exact index name, no wildcard, no comma list, no alias pattern.
- Requires `confirmation_phrase == "delete index {index}"`.
- Index must pass allowlist and denylist checks.
