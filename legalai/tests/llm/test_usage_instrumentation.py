from types import SimpleNamespace

import pytest

from legalai.packages.llm.router import _OpenAICompatibleClient, _ProviderSpec
from legalai.packages.shared.settings import settings
from legalai.packages.shared.tenant import TenantContext, tenant_scope
from legalai.packages.usage.store import UsageStore


class _FakeCompletions:
    async def create(self, **kwargs):
        assert kwargs["model"] == "gemini-2.5-pro"
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="cevap"))],
            usage=SimpleNamespace(prompt_tokens=120, completion_tokens=30),
        )


class _FakeOpenAI:
    def __init__(self, **kwargs):
        self.chat = SimpleNamespace(completions=_FakeCompletions())


@pytest.mark.asyncio
async def test_openai_compatible_client_records_response_usage(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("openai.AsyncOpenAI", _FakeOpenAI)
    monkeypatch.setattr(settings, "usage_db_path", str(tmp_path / "usage.db"))
    client = _OpenAICompatibleClient(
        _ProviderSpec(
            provider="gemini",
            base_url="https://example.test/v1",
            model="gemini-2.5-pro",
            api_key="test-key",
        )
    )

    with tenant_scope(TenantContext("tenant-a", "A")):
        answer = await client.generate("system", "user")

    report = await UsageStore(tmp_path / "usage.db").report("2026-07", tenant_id="tenant-a")

    assert answer == "cevap"
    assert report["calls"] == 1
    assert report["input_tokens"] == 120
    assert report["output_tokens"] == 30
    assert report["cost_usd_estimate"] > 0


@pytest.mark.asyncio
async def test_usage_record_failure_does_not_hide_model_answer(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("openai.AsyncOpenAI", _FakeOpenAI)
    monkeypatch.setattr(settings, "usage_db_path", str(tmp_path / "usage.db"))

    async def broken_record(*args, **kwargs):
        raise OSError("usage store unavailable")

    monkeypatch.setattr(UsageStore, "record", broken_record)
    client = _OpenAICompatibleClient(
        _ProviderSpec("gemini", "https://example.test/v1", "gemini-2.5-pro", "test-key")
    )

    with tenant_scope(TenantContext("tenant-a", "A")):
        assert await client.generate("system", "user") == "cevap"

