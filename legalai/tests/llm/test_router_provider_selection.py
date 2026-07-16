import pytest

from legalai.packages.llm.router import LLMNotConfiguredError, LLMRouter
from legalai.packages.shared.settings import settings


class CapturingClient:
    def __init__(self, spec):
        self.provider = spec.provider
        self.model = spec.model
        self.base_url = spec.base_url


@pytest.mark.parametrize(
    ("provider", "key", "model_attr", "expected_url"),
    [
        ("openrouter", "openrouter-api-key", "openrouter-model", "https://openrouter.ai/api/v1"),
        ("deepseek", "deepseek-api-key", "deepseek-model", "https://api.deepseek.com/v1"),
    ],
)
def test_explicit_provider_uses_provider_key_url_and_model(
    monkeypatch, provider, key, model_attr, expected_url
) -> None:
    monkeypatch.setattr(settings, "legalai_llm_provider", provider)
    monkeypatch.setattr(settings, "openrouter_api_key", key if provider == "openrouter" else "")
    monkeypatch.setattr(settings, "deepseek_api_key", key if provider == "deepseek" else "")
    monkeypatch.setattr(settings, "openrouter_model", model_attr)
    monkeypatch.setattr(settings, "deepseek_model", model_attr)

    router = LLMRouter(client_factory=CapturingClient)
    client = router.route("reasoning")

    assert client.provider == provider
    assert client.model == model_attr
    assert client.base_url == expected_url


def test_explicit_gemini_route_and_auto_fallback(monkeypatch) -> None:
    monkeypatch.setattr(settings, "legalai_llm_provider", "gemini")
    monkeypatch.setattr(settings, "gemini_api_key", "gemini-key")
    monkeypatch.setattr(settings, "gemini_model", "gemini-custom")
    explicit = LLMRouter(client_factory=CapturingClient).route("simple")

    monkeypatch.setattr(settings, "legalai_llm_provider", "auto")
    auto = LLMRouter(client_factory=CapturingClient).route("simple")

    assert explicit.provider == "gemini"
    assert explicit.model == "gemini-custom"
    assert auto.provider == "gemini"


def test_missing_explicit_provider_names_setting_without_secret(monkeypatch) -> None:
    monkeypatch.setattr(settings, "legalai_llm_provider", "openrouter")
    monkeypatch.setattr(settings, "openrouter_api_key", "")

    with pytest.raises(LLMNotConfiguredError, match="OPENROUTER_API_KEY"):
        LLMRouter(client_factory=CapturingClient).route("simple")
