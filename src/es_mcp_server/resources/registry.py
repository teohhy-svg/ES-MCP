"""MCP resource registration for read-only Elasticsearch context."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from uuid import uuid4

from mcp.server.fastmcp import FastMCP
from pydantic import ValidationError

from es_mcp_server.config import Settings
from es_mcp_server.es_client import ElasticsearchService, create_elasticsearch_client
from es_mcp_server.models.common import ErrorResponse, ErrorType
from es_mcp_server.models.tools import (
    ClusterHealthRequest,
    IndexMappingRequest,
    IndexSettingsRequest,
    ListIndicesRequest,
)
from es_mcp_server.security import SecurityError, mask_sensitive_value


def register_resources(mcp: FastMCP, settings: Settings) -> None:
    """Register required read-only MCP resources."""

    service = ElasticsearchService(create_elasticsearch_client(settings), settings)

    @mcp.resource("elasticsearch://cluster/health")
    def elasticsearch_cluster_health() -> dict[str, Any]:
        """Read Elasticsearch cluster health."""

        return _run_resource(lambda: service.cluster_health(ClusterHealthRequest()))

    @mcp.resource("elasticsearch://indices")
    def elasticsearch_indices() -> dict[str, Any]:
        """Read allowed Elasticsearch index summaries."""

        return _run_resource(lambda: service.list_indices(ListIndicesRequest()))

    @mcp.resource("elasticsearch://indices/{index}/mapping")
    def elasticsearch_index_mapping(index: str) -> dict[str, Any]:
        """Read mapping for an allowed Elasticsearch index."""

        return _run_resource(lambda: service.index_mapping(IndexMappingRequest(index=index)))

    @mcp.resource("elasticsearch://indices/{index}/settings")
    def elasticsearch_index_settings(index: str) -> dict[str, Any]:
        """Read settings for an allowed Elasticsearch index."""

        return _run_resource(lambda: service.index_settings(IndexSettingsRequest(index=index)))


def _run_resource(action: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    try:
        return action()
    except ValidationError as exc:
        return _resource_error(ErrorType.VALIDATION_ERROR, str(exc))
    except SecurityError as exc:
        return _resource_error(ErrorType.SECURITY_DENIED, str(exc))
    except Exception as exc:  # pragma: no cover - concrete errors depend on runtime/ES
        return _resource_error(ErrorType.ELASTICSEARCH_ERROR, str(exc))


def _resource_error(error_type: ErrorType, message: str) -> dict[str, Any]:
    return {
        "error": ErrorResponse(
            error_type=error_type,
            message=str(mask_sensitive_value(message)),
            request_id=str(uuid4()),
        ).model_dump(mode="json")
    }
