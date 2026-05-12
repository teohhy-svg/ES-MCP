# ES-MCP

Production-grade Model Context Protocol server for safe Elasticsearch access from AI clients such as Codex, Claude Desktop, and ChatGPT MCP clients.

Current status: Phase 6 is complete with Phase 5 intentionally skipped. The repository contains the architecture harness, Python package, read-only MCP tools, MCP resources, MCP prompts, Docker/full-stack hosting guidance, MCP client examples, and focused tests.

## Mission
ES-MCP will allow AI clients to safely interact with Elasticsearch for:

- Cluster health and node summaries
- Index discovery, mappings, and settings
- Guarded search and limited DSL search
- Observability workflows for logs, error trends, slow queries, shards, and snapshots
- Optional index creation and deletion are out of scope for the current read-only build

The default posture is read-only, auditable, and conservative.

## Safety Model
The server is designed around these defaults:

- Read-only mode enabled by default
- Dangerous operations disabled unless explicitly enabled by environment variables
- No raw unrestricted Elasticsearch query execution
- Index allowlist and denylist enforcement
- Query DSL validation with dangerous constructs blocked
- Maximum result size and timeout limits
- Credential masking in logs
- Sanitized errors returned to MCP clients
- Audit logging for every tool call

See [harness/SECURITY_MODEL.md](harness/SECURITY_MODEL.md) for the detailed security proposal.

## MCP Tools
Implemented read-only tools:

- `es_cluster_health`
- `es_nodes_summary`
- `es_list_indices`
- `es_index_mapping`
- `es_index_settings`
- `es_search`
- `es_dsl_search`
- `es_recent_logs`
- `es_error_trends`
- `es_slow_queries`
- `es_shard_allocation`
- `es_snapshot_status`

Optional write/destructive tools:

- `es_create_index`, intentionally not implemented or registered yet
- `es_delete_index`, intentionally not implemented or registered yet

See [harness/TOOL_SCHEMAS.md](harness/TOOL_SCHEMAS.md) for the proposed schemas and guardrails.

## MCP Resources
- `elasticsearch://cluster/health`
- `elasticsearch://indices`
- `elasticsearch://indices/{index}/mapping`
- `elasticsearch://indices/{index}/settings`

## MCP Prompts
- `investigate_elasticsearch_incident`
- `troubleshoot_unassigned_shards`
- `analyze_application_errors`
- `optimize_search_query`

## Architecture
Target stack:

- Python 3.11+
- Official Elasticsearch Python client
- MCP Python SDK where available
- Stdio transport by default
- Pydantic models for validation
- Structured logging and audit events
- Docker and docker-compose support
- pytest unit and integration tests

See [harness/ARCHITECTURE.md](harness/ARCHITECTURE.md) for the full architecture plan.

## Quick Start
Use Python 3.11+.

```bash
python -m pip install -e ".[dev]"
cp .env.example .env
pytest
```

Run as a local stdio MCP server:

```bash
es-mcp-server
```

Run as streamable HTTP:

```bash
MCP_TRANSPORT=streamable-http \
MCP_HTTP_HOST=0.0.0.0 \
MCP_HTTP_PORT=8000 \
es-mcp-server
```

The HTTP endpoint is:

```text
http://localhost:8000/mcp
```

## Project Skeleton
The foundation includes:

- `pyproject.toml` package metadata and development tool configuration
- `.env.example` with safe defaults
- `src/es_mcp_server` package layout
- typed environment settings in `config.py`
- structured logging and secret masking helpers
- MCP tool registration plus placeholder resource and prompt registries
- Docker and docker-compose skeleton files
- pytest coverage for configuration, masking, guardrails, and query builders

Phase 3 adds registered read-only MCP tools for cluster health, nodes, indices, search, observability, shards, and snapshots.

Phase 4 adds MCP resources and investigation prompt templates.

Phase 6 adds flexible hosting guidance, MCP client examples, Docker/full-stack instructions, and additional tests.

## Development Phases
1. Architecture and harness files
2. Project skeleton and configuration
3. Read-only MCP tools
4. MCP resources and prompts
5. Optional write/destructive tools with strict safety controls, skipped for now
6. Tests, Docker, documentation, and MCP client examples

## Hosting Options
Detailed guidance lives in [docs/HOSTING.md](docs/HOSTING.md).

Container only, using an existing Elasticsearch cluster:

```bash
docker build -t es-mcp-server .
docker run --rm -i --env-file .env es-mcp-server
```

Container only over streamable HTTP:

```bash
docker run --rm \
  --env-file .env \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_HTTP_HOST=0.0.0.0 \
  -p 8000:8000 \
  es-mcp-server
```

Full stack local Elasticsearch plus ES-MCP:

```bash
docker compose --profile fullstack up --build
```

## MCP Client Examples
Examples live in [examples](examples):

- [codex-stdio.toml](examples/codex-stdio.toml)
- [codex-http.toml](examples/codex-http.toml)
- [claude-desktop-stdio.json](examples/claude-desktop-stdio.json)
- [claude-desktop-http.json](examples/claude-desktop-http.json)
- [mcp-project.json](examples/mcp-project.json)

Codex stdio:

```bash
codex mcp add es-mcp \
  --env ELASTICSEARCH_URL=http://localhost:9200 \
  --env ES_READ_ONLY=true \
  -- es-mcp-server
```

Codex HTTP:

```bash
codex mcp add es-mcp --url http://127.0.0.1:8000/mcp
```

Claude Desktop can use the JSON snippets in `examples/`. For stdio, set `command` to the full path of `es-mcp-server` if it is not on Claude Desktop's `PATH`.

## Environment Variables
| Variable | Default | Purpose |
| --- | --- | --- |
| `ELASTICSEARCH_URL` | required | Elasticsearch endpoint |
| `ELASTICSEARCH_USERNAME` | unset | Basic auth username |
| `ELASTICSEARCH_PASSWORD` | unset | Basic auth password |
| `ELASTICSEARCH_API_KEY` | unset | API key auth |
| `ELASTICSEARCH_CA_CERT_PATH` | unset | CA certificate path for TLS |
| `MCP_TRANSPORT` | `stdio` | `stdio` or `streamable-http` |
| `MCP_HTTP_HOST` | `127.0.0.1` | HTTP bind host |
| `MCP_HTTP_PORT` | `8000` | HTTP bind port |
| `MCP_HTTP_PATH` | `/mcp` | Streamable HTTP path |
| `ES_READ_ONLY` | `true` | Read-only safety posture |
| `ES_INDEX_ALLOWLIST` | `*` | Allowed index patterns |
| `ES_INDEX_DENYLIST` | system indices | Denied index patterns |
| `ES_MAX_RESULT_SIZE` | `100` | Maximum search/list result size |
| `ES_MAX_TIMEOUT_SECONDS` | `30` | Maximum request timeout |
| `ES_LOG_INDEX_PATTERN` | `logs-*` | Default log index pattern |
| `ES_SLOW_LOG_INDEX_PATTERN` | unset | Slow-log index pattern |

## Kibana Dashboards
This MCP server connects to Elasticsearch, not Kibana. It can query and analyze the underlying Elasticsearch indices that power a Kibana dashboard, but it does not currently read dashboard layout, panels, saved searches, Lens configuration, or saved object metadata.

Kibana dashboards are saved objects managed through Kibana APIs. This project intentionally denies `.kibana*` system indices by default, and Elastic warns not to write directly to the `.kibana` index. A future read-only Kibana extension could support `KIBANA_URL` and Kibana saved object export/read APIs, but that should be a separate guarded capability.

## Harness Engineering
Specialist role files live in [harness](harness):

- Product Owner
- Solution Architect
- MCP Protocol Engineer
- Elasticsearch Engineer
- Security Engineer
- Observability Engineer
- Test Engineer
- DevOps Engineer
- Documentation Engineer

Each role defines mission, responsibilities, non-responsibilities, inputs, outputs, boundaries, quality gates, acceptance criteria, and example tasks.

## Testing
The test strategy includes:

- Unit tests for configuration and security guardrails
- Mocked tool tests for Elasticsearch interactions
- MCP registration smoke tests
- Opt-in docker-compose integration tests against Elasticsearch
- CI gates for formatting, linting, typing, tests, and Docker build

```bash
pytest
ES_MCP_RUN_INTEGRATION=1 pytest -m integration
```

See [harness/TEST_PLAN.md](harness/TEST_PLAN.md).

## Documentation
- [Hosting Guide](docs/HOSTING.md)
- [Architecture](harness/ARCHITECTURE.md)
- [Security Model](harness/SECURITY_MODEL.md)
- [Tool Schemas](harness/TOOL_SCHEMAS.md)
- [Test Plan](harness/TEST_PLAN.md)

## Repository Status
This repo is intentionally read-only for now. Phase 5 write/destructive tools remain skipped.
