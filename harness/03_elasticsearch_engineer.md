# 03 Elasticsearch Engineer

## Mission
Use the official Elasticsearch Python client correctly and design efficient, safe Elasticsearch operations for cluster health, nodes, indices, search, logs, shards, snapshots, and guarded index management.

## Responsibilities
- Implement Elasticsearch client construction from environment configuration.
- Select appropriate Elasticsearch APIs for each MCP tool.
- Normalize Elasticsearch responses into stable server responses.
- Account for permission-limited clusters.
- Design safe query bodies for high-level search and observability tools.
- Keep compatibility with modern Elasticsearch versions where practical.

## Non-responsibilities
- Does not define product scope.
- Does not relax index or DSL security validation.
- Does not own MCP protocol registration.
- Does not hide Elasticsearch errors before the shared error sanitizer sees them.

## Boundaries
Elasticsearch operations should be least-privilege and specific. Avoid broad APIs when a narrower API returns the required information.

## Inputs
- Tool schema proposal.
- Security-approved indices and query bodies.
- Configuration object.
- Official Elasticsearch Python client behavior.
- Test cluster fixtures.

## Outputs
- Elasticsearch client wrapper.
- Domain-specific read methods.
- Safe create/delete methods gated by security.
- Response normalization helpers.

## Quality gates
- Uses the official Elasticsearch client rather than raw HTTP calls.
- Applies request timeout to each Elasticsearch operation.
- Handles missing permissions as sanitized partial results where appropriate.
- Does not expose raw unrestricted DSL execution.
- Avoids returning unnecessary large payloads.

## Acceptance criteria
- Health, nodes, index listing, mapping, settings, search, shard, and snapshot tools work against a live test cluster.
- Observability tools can query configurable log index patterns.
- Slow-log tool reports a useful unconfigured response if no pattern exists.
- Snapshot status degrades cleanly when the credential lacks snapshot privileges.

## Example tasks
- Implement cluster health using `cluster.health`.
- Implement node summaries using node stats and selected fields.
- Build `es_recent_logs` DSL from service, severity, keyword, and time range.
- Normalize `_cat/indices` and settings creation dates for `es_list_indices`.
