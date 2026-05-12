# Test Plan Proposal

## Mission
Prove that the Elasticsearch MCP server is safe, predictable, and useful before it is connected to real clusters.

## Test Layers
- Unit tests for configuration, validation, security guardrails, audit helpers, and response normalization.
- Tool tests using mocked Elasticsearch client responses.
- Resource and prompt registration tests.
- Integration tests against docker-compose Elasticsearch.
- Packaging and smoke tests for local stdio execution.

## Unit Test Coverage
Configuration:
- Loads required `ELASTICSEARCH_URL`.
- Supports username/password, API key, CA path, and timeout.
- Defaults to read-only mode.
- Rejects invalid numeric limits.

Index validation:
- Accepts safe exact index names.
- Accepts safe wildcard patterns for read-only operations.
- Rejects empty, whitespace, traversal, URL-like, comma-list, and destructive wildcard inputs.
- Enforces allowlist and denylist precedence.

DSL validation:
- Accepts the approved DSL subset.
- Rejects `script`, `script_score`, `function_score`, `runtime_mappings`, `regexp`, `query_string`, `knn`, `collapse`, `suggest`, `profile`, and `explain`.
- Rejects leading wildcard and too-short wildcard patterns.
- Caps `size`, timeout, and pagination.
- Traverses nested dictionaries and lists recursively.

Write safety:
- `es_create_index` denied unless write flag is enabled.
- `es_create_index` requires explicit confirmation.
- `es_delete_index` denied unless destructive flag is enabled.
- `es_delete_index` rejects wildcard and requires exact confirmation phrase.

Error handling:
- Elasticsearch exceptions map to sanitized MCP errors.
- Credentials are masked in logs and errors.

Audit:
- Audit event emitted for start, success, denial, and failure.
- Audit fields do not contain document bodies or credentials.

## Tool Tests With Mocked Elasticsearch
Read-only tools:
- `es_cluster_health` normalizes cluster health response.
- `es_nodes_summary` extracts node roles, JVM memory, CPU, and disk fields.
- `es_list_indices` merges cat indices and settings creation dates where available.
- `es_index_mapping` and `es_index_settings` apply index policy.
- `es_search` builds safe query bodies for query string, match, fields, sort, and time range.
- `es_dsl_search` enforces DSL validation before client execution.
- `es_recent_logs` and `es_error_trends` require bounded time ranges.
- `es_slow_queries` reports unconfigured state when no slow-log pattern exists.
- `es_shard_allocation` handles permission-limited explain calls.
- `es_snapshot_status` handles permission-limited repository calls.

Optional tools:
- `es_create_index` calls the official client only after all guards pass.
- `es_delete_index` calls delete only after destructive flag and phrase checks pass.

## Resource Tests
Resources:
- `elasticsearch://cluster/health`
- `elasticsearch://indices`
- `elasticsearch://indices/{index}/mapping`
- `elasticsearch://indices/{index}/settings`

Assertions:
- Resources are registered with the MCP server.
- Resource handlers reuse the same service/security layer as tools.
- Invalid index resource paths are rejected safely.

## Prompt Tests
Prompts:
- `investigate_elasticsearch_incident`
- `troubleshoot_unassigned_shards`
- `analyze_application_errors`
- `optimize_search_query`

Assertions:
- Prompts are registered.
- Prompts guide the model to call safe read-only tools first.
- Prompts include enough user variables to be useful without embedding credentials or unsafe instructions.

## Integration Test Pattern
docker-compose services:
- `elasticsearch` single-node test cluster.
- Optional `es-mcp-server` container.

Integration scenarios:
- Start Elasticsearch.
- Create test indices and sample log documents through setup fixtures.
- Run read-only tools against live cluster.
- Verify write tools are unavailable by default.
- Enable write tools in a dedicated test and create a temporary index.
- Enable destructive tools only in a dedicated isolated test and delete the temporary index with confirmation phrase.

Integration tests should be opt-in with a marker such as:
```text
pytest -m integration
```

## MCP Client Smoke Tests
- Start server over stdio.
- Verify initialize/list tools/list resources/list prompts works.
- Call `es_cluster_health` through MCP transport.
- Verify sanitized error response for an intentionally invalid index.

## CI Quality Gates
- `ruff check`
- `ruff format --check`
- `mypy`
- `pytest`
- Optional `pytest -m integration`
- Docker image build

## Test Acceptance Criteria
- Security guardrails have focused unit tests before broad feature tests.
- Tool tests do not require live Elasticsearch.
- Integration tests can run from docker-compose without external services.
- Dangerous operations are denied in default test configuration.
- At least one audit event is asserted for every tool category.
