# Hosting Guide

ES-MCP supports two practical hosting modes:

- Local stdio for desktop/agent MCP clients that launch the server process.
- Streamable HTTP for Docker, full-stack compose, and remote MCP clients.

Phase 5 write/destructive tools are intentionally skipped. All examples keep the server read-only.
Kibana support is optional and enabled only when `KIBANA_URL` is configured.

## Configuration
Copy the example environment and edit the Elasticsearch connection:

```bash
cp .env.example .env
```

Required:

```bash
ELASTICSEARCH_URL=http://localhost:9200
```

Optional authentication:

```bash
ELASTICSEARCH_USERNAME=elastic
ELASTICSEARCH_PASSWORD=change-me
```

or:

```bash
ELASTICSEARCH_API_KEY=base64-api-key
```

HTTP hosting:

```bash
MCP_TRANSPORT=streamable-http
MCP_HTTP_HOST=0.0.0.0
MCP_HTTP_PORT=8000
MCP_HTTP_PATH=/mcp
```

Optional Kibana read-only dashboard support:

```bash
KIBANA_URL=http://localhost:5601
KIBANA_SPACE_ID=default
```

## Local Stdio
Use stdio when the MCP client can launch this server as a subprocess.

```bash
python -m pip install -e ".[dev]"
cp .env.example .env
es-mcp-server
```

For stdio, keep:

```bash
MCP_TRANSPORT=stdio
```

## Docker Container Only
Use this when Elasticsearch is already running elsewhere.

Build:

```bash
docker build -t es-mcp-server .
```

Run over stdio:

```bash
docker run --rm -i \
  --env-file .env \
  es-mcp-server
```

Run over streamable HTTP:

```bash
docker run --rm \
  --env-file .env \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_HTTP_HOST=0.0.0.0 \
  -e MCP_HTTP_PORT=8000 \
  -p 8000:8000 \
  es-mcp-server
```

The HTTP MCP endpoint is:

```text
http://localhost:8000/mcp
```

## Full Stack With Docker Compose
Use this when you want a local Elasticsearch test cluster plus the MCP server.

Start Elasticsearch only:

```bash
docker compose up elasticsearch
```

Start Elasticsearch plus ES-MCP over HTTP:

```bash
docker compose --profile fullstack up --build
```

Start Elasticsearch, Kibana, and ES-MCP over HTTP:

```bash
docker compose --profile fullstack-kibana up --build
```

The MCP endpoint is:

```text
http://localhost:8000/mcp
```

The Elasticsearch endpoint is:

```text
http://localhost:9200
```

The Kibana endpoint is:

```text
http://localhost:5601
```

## Production Notes
- Prefer least-privileged Elasticsearch credentials with monitor/read privileges only.
- Keep `ES_READ_ONLY=true`.
- Keep `ES_ENABLE_WRITE_TOOLS=false` and `ES_ENABLE_DESTRUCTIVE_TOOLS=false`.
- Restrict `ES_INDEX_ALLOWLIST` to the indices the AI client actually needs.
- Keep `.kibana*` and `.security*` denied unless a separately reviewed feature requires them.
- Put HTTP deployments behind your normal internal network controls or an MCP gateway.
- Use TLS and `ELASTICSEARCH_CA_CERT_PATH` when connecting to secured Elasticsearch.
- Configure `KIBANA_URL` only when the MCP client needs dashboard saved-object context.
- Use Kibana read-only privileges for dashboard and saved-object access.
- Do not grant this server Kibana write, import, export, or delete privileges unless a separately
  reviewed feature adds those capabilities.

## Integration Test Pattern
The intended integration loop is:

```bash
docker compose up -d elasticsearch
python -m pip install -e ".[dev]"
ES_MCP_RUN_INTEGRATION=1 pytest -m integration
```

Integration tests are opt-in so unit tests remain fast and do not require Docker.
