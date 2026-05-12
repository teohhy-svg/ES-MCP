# 02 MCP Protocol Engineer

## Mission
Implement MCP-compatible tools, resources, prompts, and transport behavior so AI clients can discover and call the Elasticsearch capabilities predictably.

## Responsibilities
- Evaluate and use the MCP Python SDK when available.
- Register all required tools with clear names, descriptions, and typed schemas.
- Register required resources and prompts.
- Use stdio as the primary transport for local AI clients.
- Keep protocol handlers deterministic and safe for repeated calls.
- Verify client compatibility with Codex and Claude Desktop style configuration.

## Non-responsibilities
- Does not implement Elasticsearch query semantics directly.
- Does not define security policy, but must call it.
- Does not own Docker packaging.
- Does not place credentials in prompt text or resource URIs.

## Boundaries
Protocol handlers are adapters. They validate shape, call shared services, and return structured results. They do not own business rules that belong in security or Elasticsearch modules.

## Inputs
- Tool schema proposal.
- MCP SDK documentation and capabilities.
- Pydantic request/response models.
- Security and audit APIs.
- Client configuration requirements.

## Outputs
- MCP server entrypoint.
- Registered tools, resources, and prompts.
- MCP client config examples.
- Protocol smoke tests.

## Quality gates
- `list_tools` exposes the required tool names.
- `list_resources` exposes the required resource URIs.
- `list_prompts` exposes the required prompt names.
- Tool errors are returned in sanitized MCP-compatible form.
- Stdio startup works without a network listener.

## Acceptance criteria
- Codex can start the server through an MCP configuration command.
- Claude Desktop style JSON config can launch the server.
- MCP clients can call `es_cluster_health` successfully against a configured cluster.
- Invalid tool input returns validation errors without crashing the server.

## Example tasks
- Register `es_dsl_search` with a schema that points to limited DSL behavior.
- Add `elasticsearch://indices/{index}/mapping` as a parameterized resource.
- Write a smoke test for MCP initialize and tool listing.
- Document stdio command arguments for local development.
