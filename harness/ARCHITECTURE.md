# Elasticsearch MCP Server Architecture

## Mission
Build a production-grade Model Context Protocol server that lets AI clients safely inspect, search, troubleshoot, and selectively manage Elasticsearch clusters.

The server is designed for Codex, Claude Desktop, ChatGPT MCP clients, and other MCP-compatible clients. Its default posture is read-only, auditable, and conservative.

## Target Runtime
- Python 3.11+
- Official `elasticsearch` Python client
- MCP Python SDK as the primary protocol layer when available
- Stdio transport as the default MCP transport for desktop and agent clients
- Optional HTTP/FastAPI adapter only if MCP SDK support and client compatibility require it
- Pydantic models for all tool inputs and structured outputs
- Structured JSON logging with credential masking
- Docker and docker-compose support
- `.env` configuration loaded at process start

## Proposed Project Structure
```text
/
  README.md
  pyproject.toml
  .env.example
  Dockerfile
  docker-compose.yml
  src/es_mcp_server/
    __init__.py
    main.py
    config.py
    security.py
    audit.py
    es_client.py
    tools/
      __init__.py
      cluster.py
      indices.py
      search.py
      observability.py
      shards.py
      snapshots.py
      write.py
    resources/
      __init__.py
      registry.py
    prompts/
      __init__.py
      registry.py
    models/
      __init__.py
      common.py
      tools.py
      responses.py
  tests/
    unit/
    integration/
  harness/
```

## Module Responsibilities
- `main.py`: Builds the MCP server, registers tools/resources/prompts, configures logging, and starts the selected transport.
- `config.py`: Owns environment parsing, default values, feature flags, and validation of deployment settings.
- `security.py`: Owns index name validation, allowlist/denylist checks, DSL validation, size and timeout enforcement, and confirmation checks.
- `audit.py`: Emits structured audit events for every tool call, including allowed/blocked outcomes.
- `es_client.py`: Wraps the official Elasticsearch client, centralizes connection construction, request options, and sanitized exception mapping.
- `tools/`: Contains small, focused modules grouped by Elasticsearch domain.
- `resources/`: Registers MCP resources backed by safe read-only tool/service calls.
- `prompts/`: Registers incident, troubleshooting, error analysis, and query optimization prompts.
- `models/`: Defines Pydantic request and response contracts.

## Request Lifecycle
1. MCP client invokes a tool with JSON arguments.
2. MCP SDK routes the call to the registered handler.
3. Pydantic validates the request model.
4. Audit logging records call start with masked metadata.
5. Security layer enforces mode, index policy, query policy, size, timeout, and confirmation requirements.
6. Elasticsearch client wrapper executes the least-privileged request.
7. Handler normalizes Elasticsearch responses into stable response models.
8. Audit logging records success, denial, or sanitized failure.
9. MCP server returns structured data or a sanitized error to the client.

## Tool Groups
- Cluster and node tools: `es_cluster_health`, `es_nodes_summary`
- Index read tools: `es_list_indices`, `es_index_mapping`, `es_index_settings`
- Search tools: `es_search`, `es_dsl_search`
- Observability tools: `es_recent_logs`, `es_error_trends`, `es_slow_queries`
- Operations tools: `es_shard_allocation`, `es_snapshot_status`
- Optional write tools: `es_create_index`
- Optional destructive tools: `es_delete_index`

## MCP Resources
- `elasticsearch://cluster/health`
- `elasticsearch://indices`
- `elasticsearch://indices/{index}/mapping`
- `elasticsearch://indices/{index}/settings`

Resources are implemented as safe read-only wrappers around the same service layer used by tools.

## MCP Prompts
- `investigate_elasticsearch_incident`
- `troubleshoot_unassigned_shards`
- `analyze_application_errors`
- `optimize_search_query`

Prompts guide AI clients through safe tool usage rather than embedding hidden operations.

## Configuration Model
Required:
- `ELASTICSEARCH_URL`

Authentication options:
- `ELASTICSEARCH_USERNAME`
- `ELASTICSEARCH_PASSWORD`
- `ELASTICSEARCH_API_KEY`

TLS:
- `ELASTICSEARCH_CA_CERT_PATH`

Safety and limits:
- `ES_READ_ONLY=true`
- `ES_ENABLE_WRITE_TOOLS=false`
- `ES_ENABLE_DESTRUCTIVE_TOOLS=false`
- `ES_INDEX_ALLOWLIST=*`
- `ES_INDEX_DENYLIST=.* , .security* , .kibana*`
- `ES_MAX_RESULT_SIZE=100`
- `ES_MAX_TIMEOUT_SECONDS=30`
- `ES_REQUEST_TIMEOUT_SECONDS=10`
- `ES_LOG_INDEX_PATTERN=logs-*`
- `ES_SLOW_LOG_INDEX_PATTERN=`

## Deployment Shape
- Local MCP usage runs over stdio.
- Docker image starts the MCP server with environment configuration.
- docker-compose includes an optional Elasticsearch service for integration testing.
- Production deployments should run with least-privileged Elasticsearch credentials.

## Implementation Phases
1. Architecture and harness files only.
2. Project skeleton and configuration.
3. Read-only tools.
4. Resources and prompts.
5. Optional write and destructive tools with strict safety controls.
6. Tests, Docker, documentation, and MCP client examples.

## Architectural Acceptance Criteria
- Every tool has a typed request model and a stable structured response.
- Dangerous operations are impossible unless explicitly enabled by environment variables and confirmed per call.
- The security layer is shared by tools and resources.
- No raw unrestricted Elasticsearch query execution is exposed.
- Audit logging covers every call, denial, and error.
- Tests can run without a live Elasticsearch cluster for unit coverage.
- Integration tests can run against docker-compose Elasticsearch when requested.
