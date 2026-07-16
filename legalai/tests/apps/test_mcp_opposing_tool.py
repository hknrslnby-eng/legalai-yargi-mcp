import json
from pathlib import Path

import pytest

import legalai.apps.mcp.server as server_module
from legalai.packages.layers.opposing import OpposingResult
from legalai.packages.shared.settings import settings


@pytest.mark.asyncio
async def test_mcp_opposing_tool_delegates_without_llm(monkeypatch):
    async def fake_run_opposing(**kwargs):
        return OpposingResult(
            question=kwargs["question"],
            mode="host-orchestrated",
            role=kwargs["role"],
            position=kwargs["position"],
        )

    monkeypatch.setattr(server_module, "run_opposing", fake_run_opposing)
    payload = await server_module.agresif_karsi_taraf("alacak", "ödenmedi")

    assert payload["mode"] == "host-orchestrated"
    assert payload["analysis_only"] is True


def test_codex_and_cursor_configs_are_independent_and_secret_free():
    root = Path(__file__).resolve().parents[3]
    codex_text = (root / ".codex" / "config.toml").read_text(encoding="utf-8")
    cursor_text = (root / ".cursor" / "mcp.json").read_text(encoding="utf-8")
    cursor_payload = json.loads(cursor_text)

    assert "mcp_servers.legalai" in codex_text
    assert "mcpServers" in cursor_payload
    assert "yargi-mcp-fork" in cursor_payload["mcpServers"]
    assert "OPENROUTER_API_KEY" not in codex_text
    assert "DEEPSEEK_API_KEY" not in codex_text
    assert "localhost" not in codex_text.lower()
    assert "port" not in codex_text.lower()
