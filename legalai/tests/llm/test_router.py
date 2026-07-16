"""LLMRouter'ın hangi anahtarlar dolu ise ona göre sağlayıcı seçtiğini
doğrular — gerçek bir API çağrısı yapmaz (client_factory enjekte edilir)."""
import pytest

from legalai.packages.llm.router import LLMNotConfiguredError, LLMRouter, _ProviderSpec
from legalai.packages.shared.settings import settings


class _RecordingClient:
    def __init__(self, spec: _ProviderSpec):
        self.spec = spec


@pytest.fixture(autouse=True)
def _clear_keys(monkeypatch):
    for attr in [
        "gemini_api_key",
        "groq_api_key",
        "deepseek_api_key",
        "openai_api_key",
        "anthropic_api_key",
        "openrouter_api_key",
    ]:
        monkeypatch.setattr(settings, attr, "", raising=False)
    yield


def test_route_raises_when_no_key_configured():
    router = LLMRouter(client_factory=_RecordingClient)

    with pytest.raises(LLMNotConfiguredError):
        router.route("simple")


def test_route_simple_prefers_groq_when_both_available(monkeypatch):
    monkeypatch.setattr(settings, "groq_api_key", "gsk-test")
    monkeypatch.setattr(settings, "gemini_api_key", "gm-test")
    router = LLMRouter(client_factory=_RecordingClient)

    client = router.route("simple")

    assert client.spec.provider == "groq"


def test_route_simple_falls_back_to_gemini_when_no_groq_key(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "gm-test")
    router = LLMRouter(client_factory=_RecordingClient)

    client = router.route("simple")

    assert client.spec.provider == "gemini"


def test_route_reasoning_prefers_gemini_pro(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "gm-test")
    monkeypatch.setattr(settings, "deepseek_api_key", "ds-test")
    router = LLMRouter(client_factory=_RecordingClient)

    client = router.route("reasoning")

    assert client.spec.provider == "gemini"
    assert "pro" in client.spec.model
