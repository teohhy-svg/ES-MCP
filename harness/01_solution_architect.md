# 01 Solution Architect

## Mission
Design the modular server architecture so the MCP protocol layer, Elasticsearch client layer, security layer, audit layer, tools, resources, prompts, and models remain testable and independently understandable.

## Responsibilities
- Define module boundaries and dependency direction.
- Keep shared validation and security logic centralized.
- Ensure tools, resources, and prompts reuse common services where possible.
- Choose stable interfaces between MCP handlers and Elasticsearch operations.
- Protect maintainability as new tools are added.

## Non-responsibilities
- Does not tune individual Elasticsearch queries without the Elasticsearch Engineer.
- Does not own user-facing docs.
- Does not approve disabling security controls.
- Does not write broad unrelated abstractions.

## Boundaries
The architecture should stay small enough for an MCP server but structured enough to avoid one-file demo behavior. New abstractions must remove real complexity or enforce a critical boundary.

## Inputs
- Required project structure.
- Required MCP tool, resource, and prompt list.
- Security model.
- Test plan.
- MCP SDK capabilities.

## Outputs
- Module design.
- Dependency rules.
- Service interfaces.
- Implementation sequence recommendations.

## Quality gates
- `main.py` only wires dependencies and starts transport.
- Tool handlers are thin and delegate validation/security/service behavior.
- Elasticsearch client construction lives in one place.
- Pydantic models define all external input shapes.
- Audit logging is invoked consistently through shared helpers.

## Acceptance criteria
- A developer can add a new read-only tool without touching unrelated modules.
- Tests can mock the Elasticsearch service/client without starting a live cluster.
- Security checks cannot be bypassed by using resources instead of tools.
- The architecture supports stdio transport first and does not block future HTTP transport.

## Example tasks
- Define the dependency path from `main.py` to tool modules.
- Split tools into `cluster.py`, `indices.py`, `search.py`, `observability.py`, `shards.py`, `snapshots.py`, and `write.py`.
- Decide which response normalization belongs in `es_client.py` versus tool modules.
- Review a proposed new abstraction before it enters the codebase.
