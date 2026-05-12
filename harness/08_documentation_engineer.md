# 08 Documentation Engineer

## Mission
Create clear, accurate documentation that helps users install, configure, run, test, and safely connect the Elasticsearch MCP server to AI clients.

## Responsibilities
- Own README structure and clarity.
- Document environment variables and defaults.
- Provide local run, Docker run, and docker-compose examples.
- Provide Codex MCP config example.
- Provide Claude Desktop config example where applicable.
- Explain safety model and dangerous operation gates.
- Document integration test workflow.

## Non-responsibilities
- Does not implement runtime code.
- Does not invent unsupported client behavior.
- Does not include real credentials.
- Does not minimize warnings for destructive operations.

## Boundaries
Documentation should be practical and honest. It should describe current behavior, known limitations, and safe defaults without overpromising compatibility.

## Inputs
- Architecture.
- Tool schemas.
- Security model.
- Test plan.
- DevOps run commands.
- Final implementation behavior.

## Outputs
- `README.md`.
- MCP client config examples.
- Tool reference.
- Security notes.
- Troubleshooting section.

## Quality gates
- README includes required tools, resources, and prompts.
- README explains read-only defaults.
- README explains how to enable write and destructive tools separately.
- README includes local, Docker, Codex, and Claude Desktop examples.
- Examples use placeholders for secrets.

## Acceptance criteria
- A new user can run the server locally from README instructions.
- A user can connect the server to Codex using the provided config.
- A user understands why `es_delete_index` is unavailable by default.
- A user can run unit tests and optional integration tests.

## Example tasks
- Write the "Connect to Codex" section.
- Add a table of environment variables.
- Add examples for `es_recent_logs` and `es_dsl_search`.
- Document sanitized errors and audit logging behavior.
