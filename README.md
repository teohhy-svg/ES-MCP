# ES-MCP

Production-grade Model Context Protocol server for safe Elasticsearch access from AI clients such as Codex, Claude Desktop, and ChatGPT MCP clients.

Current status: Phase 3 is complete for read-only tools. The repository contains the architecture harness, Python package skeleton, configuration layer, Docker skeleton, read-only MCP tools, and focused configuration/security/query-builder tests. Phase 5 write/destructive tools are intentionally skipped for now.

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

## Planned MCP Resources
- `elasticsearch://cluster/health`
- `elasticsearch://indices`
- `elasticsearch://indices/{index}/mapping`
- `elasticsearch://indices/{index}/settings`

## Planned MCP Prompts
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

## Development Phases
1. Architecture and harness files
2. Project skeleton and configuration
3. Read-only MCP tools
4. MCP resources and prompts
5. Optional write/destructive tools with strict safety controls, skipped for now
6. Tests, Docker, documentation, and MCP client examples

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

## Test Plan
The planned test strategy includes:

- Unit tests for configuration and security guardrails
- Mocked tool tests for Elasticsearch interactions
- MCP registration smoke tests
- Opt-in docker-compose integration tests against Elasticsearch
- CI gates for formatting, linting, typing, tests, and Docker build

See [harness/TEST_PLAN.md](harness/TEST_PLAN.md).

## Local Development
Create a Python 3.11+ environment, install the package, and run tests:

```bash
python -m pip install -e ".[dev]"
pytest
```

Run the MCP server:

```bash
cp .env.example .env
es-mcp-server
```

## Repository Status
This repo is intentionally not yet feature-complete as an MCP server. Phase 3 establishes the read-only tool layer; resources and prompts are still planned for Phase 4.
