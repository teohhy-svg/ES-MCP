from __future__ import annotations

from es_mcp_server.security import mask_sensitive_value


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
