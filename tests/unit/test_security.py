from __future__ import annotations

import pytest

from es_mcp_server.config import Settings
from es_mcp_server.security import (
    SecurityError,
    cap_size,
    cap_timeout,
    mask_sensitive_value,
    validate_index_pattern,
    validate_limited_dsl,
    validate_repository_name,
    validate_sort,
)


def test_mask_sensitive_value_masks_known_secret_keys() -> None:
    payload = {
        "api_key": "abc123",
        "nested": {"password": "secret"},
        "safe": "visible",
    }

    assert mask_sensitive_value(payload) == {
        "api_key": "***",
        "nested": {"password": "***"},
        "safe": "visible",
    }


def test_mask_sensitive_value_masks_url_credentials_and_auth_headers() -> None:
    payload = {
        "url": "https://elastic:secret@example.com:9200",
        "header": "Bearer abc.def",
    }

    assert mask_sensitive_value(payload) == {
        "url": "https://***:***@example.com:9200",
        "header": "Bearer ***",
    }


def test_validate_index_pattern_allows_matching_allowlist() -> None:
    settings = Settings(
        _env_file=None,
        elasticsearch_url="http://localhost:9200",
        index_allowlist=["logs-*"],
    )

    assert validate_index_pattern("logs-prod", settings) == "logs-prod"


def test_validate_index_pattern_denies_hidden_indices_by_default() -> None:
    settings = Settings(_env_file=None, elasticsearch_url="http://localhost:9200")

    with pytest.raises(SecurityError, match="hidden"):
        validate_index_pattern(".security-7", settings)


def test_validate_index_pattern_denylist_beats_allowlist() -> None:
    settings = Settings(
        _env_file=None,
        elasticsearch_url="http://localhost:9200",
        index_allowlist=["*"],
        index_denylist=["logs-secret-*"],
    )

    with pytest.raises(SecurityError, match="denied"):
        validate_index_pattern("logs-secret-prod", settings)


def test_validate_index_pattern_rejects_comma_lists() -> None:
    settings = Settings(_env_file=None, elasticsearch_url="http://localhost:9200")

    with pytest.raises(SecurityError, match="comma"):
        validate_index_pattern("logs-a,logs-b", settings)


def test_cap_size_and_timeout_apply_settings_limits() -> None:
    settings = Settings(
        _env_file=None,
        elasticsearch_url="http://localhost:9200",
        max_result_size=25,
        max_timeout_seconds=5,
        request_timeout_seconds=3,
    )

    assert cap_size(100, settings) == 25
    assert cap_timeout(None, settings) == 3
    assert cap_timeout(10, settings) == 5


def test_validate_sort_rejects_unsafe_expression() -> None:
    with pytest.raises(SecurityError, match="invalid sort"):
        validate_sort(["@timestamp;desc"])


def test_validate_repository_name_rejects_wildcards() -> None:
    with pytest.raises(SecurityError, match="repository"):
        validate_repository_name("snapshots-*")


def test_validate_limited_dsl_accepts_safe_bool_query() -> None:
    dsl = {
        "query": {
            "bool": {
                "filter": [
                    {"term": {"service.name": "api"}},
                    {"range": {"@timestamp": {"gte": "now-1h"}}},
                ]
            }
        },
        "_source": ["@timestamp", "message"],
        "track_total_hits": True,
    }

    assert validate_limited_dsl(dsl) == dsl


def test_validate_limited_dsl_rejects_nested_script() -> None:
    dsl = {
        "query": {
            "bool": {
                "filter": [{"script": {"source": "doc['x'].value > 0"}}],
            }
        }
    }

    with pytest.raises(SecurityError, match="script"):
        validate_limited_dsl(dsl)


def test_validate_limited_dsl_rejects_top_level_size() -> None:
    with pytest.raises(SecurityError, match="top-level"):
        validate_limited_dsl({"query": {"match": {"message": "error"}}, "size": 10000})
