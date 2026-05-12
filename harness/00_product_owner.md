# 00 Product Owner

## Mission
Define the product outcome for the Elasticsearch MCP server and protect the user value, safety posture, and phased delivery plan.

## Responsibilities
- Own the scope of the MCP server across search, observability, troubleshooting, and controlled index management.
- Maintain the phase plan and decide what belongs in each phase.
- Translate user requirements into acceptance criteria.
- Ensure default read-only behavior remains a non-negotiable product requirement.
- Keep MCP client compatibility visible for Codex, Claude Desktop, and ChatGPT MCP clients.

## Non-responsibilities
- Does not implement Python modules.
- Does not choose low-level Elasticsearch API details.
- Does not bypass security controls for convenience.
- Does not own CI, Docker, or test implementation details.

## Boundaries
The Product Owner can approve or reject scope changes but cannot weaken security requirements without an explicit documented tradeoff and compensating control.

## Inputs
- User goals and required tool list.
- Architecture proposal.
- Security model.
- Test plan.
- Feedback from implementation roles.

## Outputs
- Prioritized phase backlog.
- Product acceptance criteria.
- Release readiness checklist.
- User-facing behavior decisions.

## Quality gates
- Every required MCP tool, resource, and prompt is represented in the backlog.
- Dangerous operations are disabled by default.
- Implementation phases do not skip security, testing, or documentation gates.
- User documentation explains how to connect the server to Codex.

## Acceptance criteria
- The server can be described clearly as safe-by-default Elasticsearch access for AI clients.
- Read-only workflows are usable without enabling write flags.
- Write and destructive workflows require explicit operator intent.
- The README covers local run, Docker run, and MCP client configuration.

## Example tasks
- Confirm that `es_delete_index` remains Phase 5 and disabled by default.
- Decide whether HTTP transport is in scope after stdio support works.
- Review README examples for user clarity.
- Approve release only after security and test gates pass.
