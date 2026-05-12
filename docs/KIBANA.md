# Kibana Extension Guide

The Kibana extension is optional and read-only. It is enabled only when `KIBANA_URL` is configured.

## What It Adds
Tools:

- `kbn_status`
- `kbn_spaces`
- `kbn_list_dashboards`
- `kbn_get_dashboard`
- `kbn_dashboard_references`

Resources:

- `kibana://status`
- `kibana://spaces`
- `kibana://dashboards`
- `kibana://dashboards/{dashboard_id}`
- `kibana://dashboards/{dashboard_id}/references`

Prompt:

- `investigate_kibana_dashboard`

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

## Safety Rules
- Kibana support is read-only.
- Do not read or write `.kibana*` indices directly.
- Do not call Kibana write, update, import, export, or delete APIs.
- Keep Kibana credentials least-privileged.
- Prefer a dedicated read-only Kibana role with dashboard and saved object read access.

## Limitations
- The dashboard list operation uses Kibana's saved-object find API, which Elastic currently
  marks as deprecated legacy API. It is still useful for read-only discovery, but a future
  version may replace it with a newer dashboard-specific listing API when Elastic provides one.
- This extension returns saved-object and panel metadata. It does not render screenshots or
  execute browser-side dashboard embeddables.
- Panel query extraction can vary by Kibana visualization type and version. Use
  `kbn_dashboard_references` as the starting point, then inspect referenced saved objects or
  underlying Elasticsearch data as needed.

## Elastic API References
- Kibana APIs: <https://www.elastic.co/docs/api/doc/kibana/>
- Kibana status API: <https://www.elastic.co/docs/api/doc/kibana/operation/operation-get-status>
- Kibana spaces API:
  <https://www.elastic.co/docs/api/doc/kibana/operation/operation-get-spaces-space>
- Saved objects find API:
  <https://www.elastic.co/docs/api/doc/kibana/operation/operation-get-saved-objects-find>
- Saved objects guidance: <https://www.elastic.co/guide/en/kibana/current/saved-objects-api.html>
