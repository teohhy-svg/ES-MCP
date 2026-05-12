"""MCP prompt templates for Elasticsearch investigation workflows."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from es_mcp_server.config import Settings


def register_prompts(mcp: FastMCP, settings: Settings) -> None:
    """Register Elasticsearch troubleshooting prompts."""

    _ = settings

    @mcp.prompt()
    def investigate_elasticsearch_incident(
        symptoms: str,
        time_range: str = "last 30 minutes",
    ) -> str:
        """Guide an incident investigation with safe read-only tools."""

        return build_investigate_incident_prompt(symptoms=symptoms, time_range=time_range)

    @mcp.prompt()
    def troubleshoot_unassigned_shards(index: str | None = None) -> str:
        """Guide diagnosis of unassigned shards."""

        return build_troubleshoot_unassigned_shards_prompt(index=index)

    @mcp.prompt()
    def analyze_application_errors(
        service: str,
        start_time: str,
        end_time: str,
        index: str | None = None,
    ) -> str:
        """Guide application error analysis over a bounded time range."""

        return build_analyze_application_errors_prompt(
            service=service,
            start_time=start_time,
            end_time=end_time,
            index=index,
        )

    @mcp.prompt()
    def optimize_search_query(
        query_or_dsl: str,
        index: str | None = None,
        goal: str = "improve safety and performance",
    ) -> str:
        """Guide review of a query and safer/faster alternatives."""

        return build_optimize_search_query_prompt(
            query_or_dsl=query_or_dsl,
            index=index,
            goal=goal,
        )


def build_investigate_incident_prompt(symptoms: str, time_range: str) -> str:
    return f"""Investigate this Elasticsearch incident using only safe read-only tools.

Symptoms:
{symptoms}

Time range:
{time_range}

Suggested workflow:
1. Call `es_cluster_health` to identify cluster status and shard pressure.
2. Call `es_nodes_summary` to inspect JVM heap, CPU, disk, and node roles.
3. Call `es_shard_allocation` if health is yellow or red, or if shards look unstable.
4. Call `es_error_trends` for the affected time range if application errors are involved.
5. Call `es_recent_logs` with service/severity/keyword filters to collect representative events.
6. Call `es_slow_queries` only if slow-log indices are configured.
7. Summarize impact, likely causes, evidence, and next read-only checks.

Rules:
- Do not call write or destructive tools.
- Prefer bounded time ranges and small result sizes.
- Explain uncertainty clearly when permissions or data are incomplete.
"""


def build_troubleshoot_unassigned_shards_prompt(index: str | None) -> str:
    scope = f"Focus on index `{index}`." if index else "Start cluster-wide, then narrow by index."
    return f"""Troubleshoot unassigned Elasticsearch shards.

Scope:
{scope}

Suggested workflow:
1. Call `es_cluster_health` and note `unassigned_shards`, `initializing_shards`, and status.
2. Call `es_shard_allocation` with `include_explanations=true`.
3. If an index is implicated, call `es_index_settings` for allocation, replica,
   and routing settings.
4. Call `es_nodes_summary` to inspect disk pressure, roles, JVM, and node availability.
5. Summarize primary cause candidates such as disk watermarks, missing nodes,
   allocation filters, replica pressure, or corrupt shards.

Rules:
- Keep the diagnosis read-only.
- Do not recommend delete/recreate steps without clearly labeling them as manual
  operator actions outside this MCP flow.
"""


def build_analyze_application_errors_prompt(
    service: str,
    start_time: str,
    end_time: str,
    index: str | None,
) -> str:
    index_line = (
        f"Use index pattern `{index}`."
        if index
        else "Use the configured log index pattern."
    )
    return f"""Analyze application errors from Elasticsearch logs.

Service:
{service}

Time range:
{start_time} to {end_time}

Index guidance:
{index_line}

Suggested workflow:
1. Call `es_error_trends` grouped by service or severity for the bounded time range.
2. Call `es_recent_logs` with `service={service}` and error severity filters.
3. Look for repeated exception types, endpoint names, deployment markers, hosts, or trace IDs.
4. If errors correlate with search latency, call `es_slow_queries` if configured.
5. Summarize top error signatures, timeline, affected components, evidence, and follow-up queries.

Rules:
- Use small result sizes for representative samples.
- Avoid exposing sensitive document fields unless the user explicitly needs them.
"""


def build_optimize_search_query_prompt(
    query_or_dsl: str,
    index: str | None,
    goal: str,
) -> str:
    index_line = f"Target index or pattern: `{index}`." if index else "No target index supplied."
    return f"""Review this Elasticsearch query for safer and faster alternatives.

Goal:
{goal}

{index_line}

Query or DSL:
```json
{query_or_dsl}
```

Suggested workflow:
1. Identify risky constructs such as scripts, regex, query_string, leading
   wildcards, large size, deep pagination, broad source fields, or expensive
   aggregations.
2. If an index is supplied, call `es_index_mapping` to verify field types before suggesting changes.
3. Prefer `es_search` high-level parameters when possible.
4. Use `es_dsl_search` only for the allowed DSL subset and keep result size bounded.
5. Suggest concrete safer alternatives, expected tradeoffs, and validation steps.

Rules:
- Do not execute the query until it passes the safety review.
- Preserve the user's intent while reducing cluster risk.
"""
