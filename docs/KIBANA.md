# Kibana Extension Guide

The Kibana extension is optional and read-only. It is enabled only when `KIBANA_URL` is configured.

## What It Adds
Tools:

- `kbn_status`
- `kbn_spaces`
- `kbn_list_dashboards`
- `kbn_get_dashboard`
- `kbn_dashboard_references`
- `kbn_capability_report`
- `kbn_alerting_health`
- `kbn_rule_types`
- `kbn_list_rules`
- `kbn_get_rule`
- `kbn_rule_query`
- `kbn_list_connectors`
- `kbn_list_cases`
- `kbn_get_case`
- `kbn_case_alerts`
- `kbn_case_activity`
- `kbn_list_workflows`
- `kbn_get_workflow`
- `kbn_workflow_executions`
- `kbn_workflow_connectors`
- `kbn_list_ai_agents`
- `kbn_get_ai_agent`
- `kbn_list_ai_tools`
- `kbn_list_fleet_agents`

Resources:

- `kibana://status`
- `kibana://spaces`
- `kibana://dashboards`
- `kibana://dashboards/{dashboard_id}`
- `kibana://dashboards/{dashboard_id}/references`
- `kibana://capabilities`
- `kibana://alerting/health`
- `kibana://rules`
- `kibana://connectors`
- `kibana://cases`
- `kibana://cases/{case_id}/alerts`
- `kibana://workflows`
- `kibana://agents/ai`
- `kibana://agents/fleet`

Prompt:

- `investigate_kibana_dashboard`
- `investigate_alert_to_case`
- `troubleshoot_workflow_execution`

## Configuration
Minimal:

```bash
KIBANA_URL=http://localhost:5601
KIBANA_SPACE_ID=default
```

Basic auth:

```bash
KIBANA_USERNAME=elastic
KIBANA_PASSWORD=change-me
```

API key:

```bash
KIBANA_API_KEY=base64-api-key
```

TLS:

```bash
KIBANA_CA_CERT_PATH=/path/to/kibana_ca.crt
```

If Kibana-specific auth is not supplied, the HTTP client falls back to the configured
Elasticsearch auth. This is convenient for single Elastic deployments where the same
principal can read both Elasticsearch and Kibana.

## Dashboard Investigation Workflow
1. Call `kbn_status` to verify Kibana and saved objects are available.
2. Call `kbn_spaces` if the dashboard may live outside the default space.
3. Call `kbn_list_dashboards` with a title search if the dashboard ID is unknown.
4. Call `kbn_get_dashboard` to inspect the saved object.
5. Call `kbn_dashboard_references` to identify panels and referenced Lens, search, map,
   or data-view objects.
6. Use Elasticsearch tools against allowed data indices to inspect the data behind the panels.

## General Elastic Operations Workflow

1. Call `kbn_capability_report` first. It probes documented read endpoints and reports:
   - `available`: the principal can read the endpoint.
   - `permission_denied`: the endpoint exists but returned HTTP 401 or 403.
   - `unavailable`: HTTP 404, commonly an unsupported version, missing plugin, or unavailable
     licensed feature.
   - `error`: another HTTP or transport failure that needs separate investigation.
2. Call `kbn_alerting_health`, then discover and inspect rules with `kbn_list_rules`,
   `kbn_get_rule`, and `kbn_rule_query`.
3. Map rule actions to `kbn_list_connectors`.
4. Trace workflow dependencies and failures with `kbn_get_workflow`,
   `kbn_workflow_connectors`, and `kbn_workflow_executions`.
5. Inspect Agent Builder agents/tools or Fleet agents when those systems are in the path.
6. Verify downstream case state, attached alerts, and history with `kbn_list_cases`,
   `kbn_get_case`, `kbn_case_alerts`, and `kbn_case_activity`.

`kbn_rule_query` only uses query-inspector `mode=build`; it does not execute the generated
Elasticsearch query.

## Safety Rules
- Kibana support is read-only.
- Do not read or write `.kibana*` indices directly.
- Do not call Kibana write, update, import, export, or delete APIs.
- Do not enable, disable, mute, run, create, or modify rules, workflows, agents, connectors,
  cases, or Fleet agents.
- Keep Kibana credentials least-privileged.
- Prefer a dedicated read-only Kibana role with only the required feature privileges.
- Connector responses are masked recursively even though the documented list API does not
  return connector secrets.

## Limitations
- The dashboard list operation uses Kibana's saved-object find API, which Elastic currently
  marks as deprecated legacy API. It is still useful for read-only discovery, but a future
  version may replace it with a newer dashboard-specific listing API when Elastic provides one.
- This extension returns saved-object and panel metadata. It does not render screenshots or
  execute browser-side dashboard embeddables.
- Panel query extraction can vary by Kibana visualization type and version. Use
  `kbn_dashboard_references` as the starting point, then inspect referenced saved objects or
  underlying Elasticsearch data as needed.
- Workflows APIs are documented as generally available in Kibana 9.4. Older targets can return
  `unavailable` from the capability report.
- Agent Builder API access depends on Kibana version, license, feature configuration, and the
  `agentBuilder:read` privilege.
- Kibana does not expose one universal public read endpoint for every solution's alert
  documents. This server therefore covers the generic alerting framework and rules without
  bypassing Kibana by reading hidden `.alerts-*` indices. Solution-specific alert search can
  be added later as explicitly scoped modules.

## Elastic API References
- Kibana APIs: <https://www.elastic.co/docs/api/doc/kibana/>
- Kibana status API: <https://www.elastic.co/docs/api/doc/kibana/operation/operation-get-status>
- Kibana spaces API:
  <https://www.elastic.co/docs/api/doc/kibana/operation/operation-get-spaces-space>
- Saved objects find API:
  <https://www.elastic.co/docs/api/doc/kibana/operation/operation-get-saved-objects-find>
- Saved objects guidance: <https://www.elastic.co/guide/en/kibana/current/saved-objects-api.html>
- Alerting health:
  <https://www.elastic.co/docs/api/doc/kibana/operation/operation-getalertinghealth>
- Find rules:
  <https://www.elastic.co/docs/api/doc/kibana/operation/operation-get-alerting-rules-find>
- Rule query inspector:
  <https://www.elastic.co/docs/api/doc/kibana/operation/operation-get-alerting-rule-id-query-inspector>
- Connectors:
  <https://www.elastic.co/docs/api/doc/kibana/operation/operation-get-actions-connectors>
- Cases:
  <https://www.elastic.co/docs/api/doc/kibana/operation/operation-findcasesdefaultspace>
- Workflows:
  <https://www.elastic.co/docs/api/doc/kibana/group/endpoint-workflows>
- Agent Builder:
  <https://www.elastic.co/docs/explore-analyze/ai-features/agent-builder/kibana-api>
- Fleet agents:
  <https://www.elastic.co/docs/api/doc/kibana/operation/operation-get-fleet-agents>
