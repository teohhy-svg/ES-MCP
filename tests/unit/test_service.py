from __future__ import annotations

from es_mcp_server.config import Settings
from es_mcp_server.es_client import ElasticsearchService
from es_mcp_server.models.tools import ClusterHealthRequest, ListIndicesRequest


class FakeCluster:
    def health(self, level: str) -> dict[str, object]:
        assert level == "cluster"
        return {
            "cluster_name": "test-cluster",
            "status": "green",
            "number_of_nodes": 2,
            "number_of_data_nodes": 1,
            "active_primary_shards": 3,
            "active_shards": 6,
            "relocating_shards": 0,
            "initializing_shards": 0,
            "unassigned_shards": 0,
            "timed_out": False,
        }


class FakeCat:
    def indices(self, **kwargs: object) -> list[dict[str, object]]:
        assert kwargs["index"] == "logs-*"
        return [
            {
                "index": "logs-a",
                "health": "green",
                "status": "open",
                "docs.count": "10",
                "store.size": "1kb",
            },
            {
                "index": "logs-b",
                "health": "yellow",
                "status": "open",
                "docs.count": "20",
                "store.size": "2kb",
            },
        ]


class FakeIndices:
    def get_settings(self, **kwargs: object) -> dict[str, object]:
        assert kwargs["index"] == "logs-*"
        return {
            "logs-a": {"settings": {"index.creation_date": "1"}},
            "logs-b": {"settings": {"index.creation_date": "2"}},
        }


class FakeClient:
    cluster = FakeCluster()
    cat = FakeCat()
    indices = FakeIndices()

    def options(self, **kwargs: object) -> "FakeClient":
        assert "request_timeout" in kwargs
        return self


def test_cluster_health_normalizes_response() -> None:
    settings = Settings(_env_file=None, elasticsearch_url="http://localhost:9200")
    service = ElasticsearchService(FakeClient(), settings)  # type: ignore[arg-type]

    result = service.cluster_health(ClusterHealthRequest())

    assert result["cluster_name"] == "test-cluster"
    assert result["status"] == "green"
    assert result["active_shards"] == 6


def test_list_indices_applies_size_cap_and_creation_dates() -> None:
    settings = Settings(
        _env_file=None,
        elasticsearch_url="http://localhost:9200",
        max_result_size=1,
    )
    service = ElasticsearchService(FakeClient(), settings)  # type: ignore[arg-type]

    result = service.list_indices(ListIndicesRequest(pattern="logs-*", size=20))

    assert result["truncated"] is True
    assert len(result["indices"]) == 1
    assert result["indices"][0]["creation_date"] == "1"
