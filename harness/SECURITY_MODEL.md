# Security Model Proposal

## Default Posture
The server is read-only by default. Write and destructive operations are registered only when their environment flags are explicitly enabled, and each dangerous call still requires per-request confirmation.

Default environment:
```text
ES_READ_ONLY=true
ES_ENABLE_WRITE_TOOLS=false
ES_ENABLE_DESTRUCTIVE_TOOLS=false
ES_MAX_RESULT_SIZE=100
ES_MAX_TIMEOUT_SECONDS=30
ES_REQUEST_TIMEOUT_SECONDS=10
```

## Threat Model
Primary risks:
- Prompt-injected tool calls attempting destructive Elasticsearch actions.
- Exfiltration of hidden or security indices.
- Expensive queries that degrade cluster health.
- Scripted DSL, runtime fields, regex, or broad wildcard searches.
- Credential leakage through logs or client-visible errors.
- Accidental deletion via wildcard or alias-like names.

## Authentication and Transport
- The Elasticsearch client supports URL, username/password, API key, CA certificate path, and request timeout.
- API key and password must never be logged.
- TLS verification is controlled by the official client and CA path configuration.
- MCP stdio transport avoids exposing a network listener by default.
- Any future HTTP transport must require explicit binding configuration and clear deployment guidance.

## Credential Masking
All logs and audit events mask:
- URLs containing credentials.
- `ELASTICSEARCH_PASSWORD`
- `ELASTICSEARCH_API_KEY`
- Authorization headers.
- Elasticsearch error metadata that may contain credentials or endpoint internals.

## Index Policy
Index names and patterns are validated before use.

Allowed syntax:
- Exact index names for mapping, settings, search, create, and delete where applicable.
- Read-only list/search tools may accept simple wildcard patterns.
- Comma-separated index lists are disabled by default unless a later explicit requirement adds safe parsing.

Rejected syntax:
- Empty values.
- Whitespace.
- Path traversal markers.
- URL separators.
- Wildcard for destructive operations.
- Hidden/system indices unless explicitly allowed.

Policy layers:
1. Basic syntax validation.
2. Denylist check.
3. Allowlist check.
4. Operation-specific rules.

Initial denylist:
```text
.*
.security*
.kibana*
.fleet*
.tasks
.async-search*
```

## Query Policy
`es_search` builds Elasticsearch DSL internally from safe parameters. It does not expose raw query execution.

`es_dsl_search` accepts only a limited subset of DSL:
- `bool`
- `match`
- `multi_match`
- `term`
- `terms`
- `range`
- `exists`
- `ids`
- `prefix`
- `simple_query_string`
- bounded `sort`
- bounded `_source`
- bounded `date_histogram` and `terms` aggregations

Blocked clauses:
- `script`
- `script_score`
- `function_score`
- `runtime_mappings`
- `regexp`
- `query_string`
- `percolate`
- `more_like_this`
- `knn`
- `collapse`
- `suggest`
- `profile`
- `explain`

Wildcard rules:
- Leading wildcards are blocked.
- Very short wildcard prefixes are blocked.
- Wildcard use may be disabled entirely by configuration if production risk is too high.

## Result and Timeout Limits
- Tool-level `size` is capped by `ES_MAX_RESULT_SIZE`.
- Search `from` is capped or rejected if it would create deep pagination risk.
- Request timeout is capped by `ES_MAX_TIMEOUT_SECONDS`.
- Time-series tools require bounded `start_time` and `end_time`.
- Aggregation bucket counts are estimated before execution where possible.

## Write Controls
`es_create_index`:
- Disabled unless `ES_ENABLE_WRITE_TOOLS=true`.
- Requires `confirm=true`.
- Rejects hidden/system index targets unless explicitly allowed.
- Rejects dangerous settings where applicable.

`es_delete_index`:
- Disabled unless `ES_ENABLE_DESTRUCTIVE_TOOLS=true`.
- Requires exact index name.
- Rejects wildcard, comma list, aliases, and hidden/system index targets by default.
- Requires confirmation phrase: `delete index {index}`.

## Error Handling
Client-visible errors are sanitized:
```text
{
  "error_type": "validation_error | security_denied | elasticsearch_error | permission_limited | timeout",
  "message": "Safe human-readable message",
  "request_id": "optional correlation id"
}
```

Internal logs may include stack traces only after masking sensitive fields.

## Audit Logging
Every tool call emits audit events:
- `tool_call_started`
- `tool_call_allowed`
- `tool_call_denied`
- `tool_call_succeeded`
- `tool_call_failed`

Audit fields:
```text
timestamp
request_id
tool_name
operation_type
index_or_pattern
principal
allowed
denial_reason
duration_ms
result_count
error_type
```

Audit logs never contain raw credentials or full document contents.

## Security Acceptance Criteria
- All tools use shared security checks instead of ad hoc validation.
- Unit tests cover allowlist, denylist, index syntax, size caps, timeout caps, DSL recursion, blocked clauses, and confirmation requirements.
- Dangerous tools remain unavailable by default.
- Sanitized errors do not reveal credentials or raw connection details.
- Audit logging covers success, validation failure, security denial, Elasticsearch error, and timeout paths.
