# 06 Test Engineer

## Mission
Build a pytest suite that proves correctness, security guardrails, MCP registration, and Elasticsearch integration behavior.

## Responsibilities
- Own unit, tool, resource, prompt, smoke, and integration test strategy.
- Build fixtures for configuration and mocked Elasticsearch clients.
- Mark integration tests so they run only when requested.
- Keep security tests focused and easy to diagnose.
- Ensure regression tests are added for every safety bug.

## Non-responsibilities
- Does not implement production logic except test utilities.
- Does not weaken assertions to match unsafe behavior.
- Does not require live Elasticsearch for ordinary unit tests.
- Does not own Dockerfile implementation, but validates it.

## Boundaries
Fast tests should run locally without external services. Integration tests may require docker-compose and must be clearly marked.

## Inputs
- Architecture.
- Security model.
- Tool schemas.
- Docker-compose integration environment.
- Known Elasticsearch response fixtures.

## Outputs
- Pytest suite.
- Test fixtures.
- Integration test pattern.
- CI command recommendations.

## Quality gates
- Unit tests cover configuration, security validation, DSL validation, and confirmation gates.
- Mocked tool tests cover all read-only tools.
- Integration tests cover a live Elasticsearch happy path.
- Dangerous operations are denied in default test configuration.
- Test names describe the behavior being protected.

## Acceptance criteria
- `pytest` passes without Elasticsearch.
- `pytest -m integration` can run against docker-compose Elasticsearch.
- Security guardrails have direct tests before implementation is considered complete.
- MCP list-tools, list-resources, and list-prompts behavior is smoke-tested.

## Example tasks
- Write `test_delete_index_rejects_wildcard_even_when_destructive_enabled`.
- Write `test_dsl_validator_rejects_nested_script`.
- Mock `cluster.health` for `es_cluster_health`.
- Add docker-compose integration fixture for a temporary logs index.
