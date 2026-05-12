from __future__ import annotations

import os

import pytest

from es_mcp_server.config import Settings
from es_mcp_server.es_client import ElasticsearchService, create_elasticsearch_client
from es_mcp_server.models.tools import ClusterHealthRequest, ListIndicesRequest


pytestmark = pytest.mark.integration


def test_live_elasticsearch_read_only_smoke() -> None:
    if os.getenv("ES_MCP_RUN_INTEGRATION") != "1":
        pytest.skip("set ES_MCP_RUN_INTEGRATION=1 to run live Elasticsearch tests")

    settings = Settings(
        _env_file=None,
        elasticsearch_url=os.getenv("ELASTICSEARCH_URL", "http://localhost:9200"),
    )
    service = ElasticsearchService(create_elasticsearch_client(settings), settings)

    health = service.cluster_health(ClusterHealthRequest())
    indices = service.list_indices(ListIndicesRequest(pattern="*", size=10))

    assert health["status"] in {"green", "yellow", "red", "unknown"}
    assert "indices" in indices
