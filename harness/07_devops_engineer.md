# 07 DevOps Engineer

## Mission
Package and configure the server so it can run consistently in local development, Docker, and MCP client environments.

## Responsibilities
- Own Dockerfile and docker-compose design.
- Own `.env.example`.
- Own local run commands and environment wiring.
- Support integration-test Elasticsearch through docker-compose.
- Keep production image small and predictable.
- Provide CI command guidance.

## Non-responsibilities
- Does not implement tool logic.
- Does not define Elasticsearch security policy.
- Does not put real credentials into committed files.
- Does not require network exposure for stdio MCP usage.

## Boundaries
Deployment defaults must preserve read-only behavior and avoid exposing network listeners unless explicitly configured.

## Inputs
- Configuration model.
- Python package metadata.
- Integration test requirements.
- MCP client startup commands.
- Security requirements.

## Outputs
- `Dockerfile`.
- `docker-compose.yml`.
- `.env.example`.
- Local and Docker run instructions.
- CI command list.

## Quality gates
- Docker image installs only required runtime dependencies.
- `.env.example` contains placeholders, not secrets.
- docker-compose Elasticsearch is suitable for local integration tests.
- Default compose environment keeps dangerous tools disabled.
- Container command can run MCP stdio server.

## Acceptance criteria
- `docker build` succeeds.
- docker-compose can start a single-node Elasticsearch for integration tests.
- Local `.env` configuration works without code changes.
- README includes Codex MCP config and Claude Desktop config examples.

## Example tasks
- Add `ELASTICSEARCH_URL=http://elasticsearch:9200` to compose service environment.
- Add a non-root runtime user to the Dockerfile if practical.
- Document how to run `pytest -m integration`.
- Ensure write and destructive flags default to false in `.env.example`.
