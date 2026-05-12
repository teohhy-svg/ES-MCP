from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_claude_desktop_examples_are_valid_json() -> None:
    for path in (
        ROOT / "examples" / "claude-desktop-stdio.json",
        ROOT / "examples" / "claude-desktop-http.json",
        ROOT / "examples" / "claude-desktop-kibana-stdio.json",
        ROOT / "examples" / "mcp-project.json",
    ):
        payload = json.loads(path.read_text())
        assert "mcpServers" in payload
        assert payload["mcpServers"]

    stdio = json.loads((ROOT / "examples" / "claude-desktop-stdio.json").read_text())
    kibana = json.loads(
        (ROOT / "examples" / "claude-desktop-kibana-stdio.json").read_text()
    )

    assert "es-mcp" in stdio["mcpServers"]
    assert "es-mcp-kibana" in kibana["mcpServers"]


def test_codex_examples_document_stdio_and_http_modes() -> None:
    stdio = (ROOT / "examples" / "codex-stdio.toml").read_text()
    http = (ROOT / "examples" / "codex-http.toml").read_text()
    kibana = (ROOT / "examples" / "codex-kibana-stdio.toml").read_text()

    assert "[mcp_servers.es-mcp]" in stdio
    assert 'command = "es-mcp-server"' in stdio
    assert 'url = "http://127.0.0.1:8000/mcp"' in http
    assert 'KIBANA_URL = "http://localhost:5601"' in kibana


def test_hosting_docs_include_container_and_fullstack_paths() -> None:
    hosting = (ROOT / "docs" / "HOSTING.md").read_text()

    assert "Docker Container Only" in hosting
    assert "Full Stack With Docker Compose" in hosting
    assert "docker compose --profile fullstack up --build" in hosting
    assert "docker compose --profile fullstack-kibana up --build" in hosting
