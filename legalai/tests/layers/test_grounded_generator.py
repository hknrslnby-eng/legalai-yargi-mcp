"""GroundedGenerator'ın gerçek bir LLM API'sine ağ çağrısı YAPMADAN,
enjekte edilen sahte bir LLMRouter ile çalıştığını doğrular."""
import pytest

from legalai.packages.layers.grounded_generator import (
    GroundedGenerator,
    build_user_prompt,
    build_system_prompt,
)
from legalai.packages.layers.pipeline import Context
from legalai.packages.llm.router import LLMNotConfiguredError
from legalai.packages.shared.types import Document


class _FakeLLMClient:
    def __init__(self, response: str):
        self.provider = "fake"
        self.model = "fake-model"
        self._response = response
        self.last_system = None
        self.last_user = None

    async def generate(self, system: str, user: str) -> str:
        self.last_system = system
        self.last_user = user
        return self._response


class _FakeRouter:
    def __init__(self, client=None, error=None):
        self._client = client
        self._error = error

    def route(self, task="simple"):
        if self._error:
            raise self._error
        return self._client


def test_build_user_prompt_wraps_documents_in_user_document_tags():
    doc = Document(id="d1", body="karar metni", citation="Yargıtay 1. HD")

    prompt = build_user_prompt("soru metni", [doc])

    assert '<user_document id="d1" citation="Yargıtay 1. HD">' in prompt
    assert "karar metni" in prompt
    assert "soru metni" in prompt


def test_build_user_prompt_includes_retry_hint_when_present():
    prompt = build_user_prompt("soru", [], retry_hint="sadece gerçek id kullan")

    assert "DÜZELTME: sadece gerçek id kullan" in prompt



def test_build_system_prompt_composes_multiple_personas_and_reasoning_rules():
    prompt = build_system_prompt(
        "hukuk", jurisdiction_ids=["hukuk", "ceza"], expert_lenses=["sozlesmeler"]
    )

    assert "hukuk" in prompt.lower()
    assert "ceza" in prompt.lower()
    assert "1. Hukuki sorun nedir?" in prompt
    assert "Temporal Legal Context" in prompt
    assert "non-binding" in prompt


@pytest.mark.asyncio
async def test_grounded_generator_sets_answer_from_llm_client(monkeypatch):
    fake_client = _FakeLLMClient("Cevap metni [#d1].")
    monkeypatch.setattr(
        "legalai.packages.layers.grounded_generator.llm_router", _FakeRouter(client=fake_client)
    )
    doc = Document(id="d1", body="karar metni")
    ctx = Context(tenant_id="test", question="soru", mode="layered", documents=[doc])

    result = await GroundedGenerator().run(ctx)

    assert result.answer == "Cevap metni [#d1]."
    assert "karar metni" in fake_client.last_user


@pytest.mark.asyncio
async def test_grounded_generator_leaves_answer_none_when_llm_not_configured(monkeypatch):
    monkeypatch.setattr(
        "legalai.packages.layers.grounded_generator.llm_router",
        _FakeRouter(error=LLMNotConfiguredError("anahtar yok")),
    )
    ctx = Context(tenant_id="test", question="soru", mode="layered")

    result = await GroundedGenerator().run(ctx)

    assert result.answer is None
    assert any(t.get("layer") == "grounded_generator" for t in result.trace)
