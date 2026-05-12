"""Elasticsearch client construction and future response/error adapters."""

from __future__ import annotations

from elasticsearch import Elasticsearch

from es_mcp_server.config import Settings


def create_elasticsearch_client(settings: Settings) -> Elasticsearch:
    """Create the official Elasticsearch client from validated settings."""

    return Elasticsearch(
        settings.elasticsearch_url,
        **settings.elasticsearch_client_options(),
    )
