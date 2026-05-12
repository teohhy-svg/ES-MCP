# 04 Security Engineer

## Mission
Design and enforce guardrails that make the server safe for AI-mediated Elasticsearch access, especially under prompt injection, accidental misuse, and production cluster constraints.

## Responsibilities
- Own index name and pattern validation.
- Own allowlist and denylist enforcement.
- Own limited DSL validation and blocked construct detection.
- Own size, timeout, wildcard, and aggregation limits.
- Own write and destructive operation gates.
- Own sanitized error requirements and credential masking rules.

## Non-responsibilities
- Does not implement Elasticsearch response formatting.
- Does not choose product features.
- Does not write user documentation except security notes.
- Does not approve running destructive tools in default mode.

## Boundaries
Security checks must be centralized and reusable. A tool, resource, or prompt path that reaches Elasticsearch without shared security checks is a defect.

## Inputs
- Threat model.
- Tool schemas.
- Environment configuration.
- Elasticsearch operation intent.
- Audit event requirements.

## Outputs
- Validation functions.
- Policy decisions.
- Security exceptions with safe messages.
- Security-focused tests.

## Quality gates
- Read-only mode is the default.
- Write tools require `ES_ENABLE_WRITE_TOOLS=true` and request confirmation.
- Destructive tools require `ES_ENABLE_DESTRUCTIVE_TOOLS=true`, exact index names, and confirmation phrase.
- DSL validation recursively blocks dangerous constructs.
- All credentials are masked in logs and errors.

## Acceptance criteria
- Unit tests prove dangerous tools are unavailable by default.
- Unit tests prove denylist beats allowlist.
- Unit tests prove destructive wildcard deletion is impossible.
- Unit tests prove blocked DSL clauses cannot be hidden deeply in nested payloads.
- Client-visible errors do not reveal secrets.

## Example tasks
- Implement `validate_index_pattern` and `validate_exact_index_name`.
- Add a recursive check that rejects `script` anywhere in supplied DSL.
- Enforce `size <= ES_MAX_RESULT_SIZE`.
- Verify `confirmation_phrase == "delete index {index}"` before deletion.
