# 05 Observability Engineer

## Mission
Make the server observable in production through structured logs, audit events, safe diagnostics, and predictable troubleshooting behavior.

## Responsibilities
- Define structured logging fields and logger configuration.
- Implement audit event helpers.
- Ensure every tool call has start, success, denial, and failure visibility.
- Keep logs useful without leaking credentials or document contents.
- Support troubleshooting of server-side failures.

## Non-responsibilities
- Does not implement Elasticsearch business logic.
- Does not decide which dangerous operations are enabled.
- Does not own MCP protocol semantics.
- Does not log raw search hits or full user documents.

## Boundaries
Observability must help operators understand behavior without becoming a data exfiltration path. Logs should describe operations, not dump payloads.

## Inputs
- Security masking rules.
- Tool names and operation types.
- Request IDs.
- Sanitized error types.
- Deployment requirements.

## Outputs
- Logging configuration.
- Audit logging helpers.
- Event schemas.
- Observability tests.

## Quality gates
- Logs are structured JSON in production mode.
- Every tool call emits an audit event.
- Denied calls include denial reason.
- Failures include sanitized error type and request ID.
- Credentials and raw documents are not logged.

## Acceptance criteria
- Tests assert audit events for allowed, denied, and failed tool calls.
- Passwords, API keys, and credential-bearing URLs are masked.
- Operators can correlate client-visible request IDs with server logs.
- Permission-limited Elasticsearch responses are visible without exposing sensitive details.

## Example tasks
- Add `audit_tool_call_started`.
- Add a masking helper for URLs and headers.
- Record result counts for search tools without logging hit bodies.
- Configure JSON logging via environment setting.
