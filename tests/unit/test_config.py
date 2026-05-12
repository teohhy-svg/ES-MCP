from __future__ import annotations

import pytest
from pydantic import ValidationError

from es_mcp_server.config import LogFormat, McpTransport, Settings


def test_settings_default_to_read_only_safety() -> None:
    settings = Settings(_env_file=None, elasticsearch_url="http://localhost:9200")

    assert settings.read_only is True
    assert settings.enable_write_tools is False
    assert settings.enable_destructive_tools is False
    assert settings.index_allowlist == ["*"]
    assert ".security*" in settings.index_denylist
    assert settings.max_result_size == 100
    assert settings.request_timeout_seconds == 10
    assert settings.mcp_transport is McpTransport.STDIO
    assert settings.mcp_http_path == "/mcp"
    assert settings.log_format is LogFormat.JSON


def test_settings_parse_index_patterns_from_comma_separated_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ELASTICSEARCH_URL", "http://localhost:9200")
    monkeypatch.setenv("ES_INDEX_ALLOWLIST", "logs-*, metrics-*")
    monkeypatch.setenv("ES_INDEX_DENYLIST", ".*, .security*")

    settings = Settings(_env_file=None)

    assert settings.index_allowlist == ["logs-*", "metrics-*"]
    assert settings.index_denylist == [".*", ".security*"]


def test_settings_reject_credentials_embedded_in_url() -> None:
    with pytest.raises(ValidationError, match="Do not embed credentials"):
        Settings(_env_file=None, elasticsearch_url="https://elastic:secret@example.com:9200")


def test_settings_require_basic_auth_pair() -> None:
    with pytest.raises(ValidationError, match="provided together"):
        Settings(
            _env_file=None,
            elasticsearch_url="http://localhost:9200",
            elasticsearch_username="elastic",
        )


def test_settings_reject_mixed_auth_modes() -> None:
    with pytest.raises(ValidationError, match="Use either ELASTICSEARCH_API_KEY"):
        Settings(
            _env_file=None,
            elasticsearch_url="http://localhost:9200",
            elasticsearch_username="elastic",
            elasticsearch_password="secret",
            elasticsearch_api_key="api-key",
        )


def test_settings_reject_write_flags_when_read_only() -> None:
    with pytest.raises(ValidationError, match="Set ES_READ_ONLY=false"):
        Settings(
            _env_file=None,
            elasticsearch_url="http://localhost:9200",
            enable_write_tools=True,
        )


def test_settings_reject_request_timeout_above_limit() -> None:
    with pytest.raises(ValidationError, match="cannot exceed"):
        Settings(
            _env_file=None,
            elasticsearch_url="http://localhost:9200",
            request_timeout_seconds=60,
            max_timeout_seconds=30,
        )


def test_settings_reject_invalid_http_path() -> None:
    with pytest.raises(ValidationError, match="MCP_HTTP_PATH"):
        Settings(
            _env_file=None,
            elasticsearch_url="http://localhost:9200",
            mcp_http_path="mcp",
        )


def test_settings_build_elasticsearch_client_options_with_api_key() -> None:
    settings = Settings(
        _env_file=None,
        elasticsearch_url="https://example.com:9200",
        elasticsearch_api_key="api-key",
        request_timeout_seconds=7,
    )

    assert settings.elasticsearch_client_options() == {
        "api_key": "api-key",
        "request_timeout": 7,
    }


def test_settings_accept_optional_kibana_url_and_auth() -> None:
    settings = Settings(
        _env_file=None,
        elasticsearch_url="http://localhost:9200",
        kibana_url="http://localhost:5601",
        kibana_username="elastic",
        kibana_password="secret",
    )

    assert settings.kibana_url == "http://localhost:5601"
    assert settings.masked_kibana_url == "http://localhost:5601"
    assert settings.kibana_client_options()["auth"] == ("elastic", "secret")


def test_settings_reject_mixed_kibana_auth_modes() -> None:
    with pytest.raises(ValidationError, match="KIBANA_API_KEY"):
        Settings(
            _env_file=None,
            elasticsearch_url="http://localhost:9200",
            kibana_url="http://localhost:5601",
            kibana_username="elastic",
            kibana_password="secret",
            kibana_api_key="api-key",
        )


def test_settings_reject_credentials_embedded_in_kibana_url() -> None:
    with pytest.raises(ValidationError, match="Do not embed credentials"):
        Settings(
            _env_file=None,
            elasticsearch_url="http://localhost:9200",
            kibana_url="http://elastic:secret@localhost:5601",
        )


def test_settings_reject_invalid_kibana_space_id() -> None:
    with pytest.raises(ValidationError, match="KIBANA_SPACE_ID"):
        Settings(
            _env_file=None,
            elasticsearch_url="http://localhost:9200",
            kibana_url="http://localhost:5601",
            kibana_space_id="Observability",
        )
