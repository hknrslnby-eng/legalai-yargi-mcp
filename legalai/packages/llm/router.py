"""LLMRouter — görevin karmaşıklığına göre hangi LLM sağlayıcısının
çağrılacağına karar verir. Bkz. FORK-KAPSAMLI-PLAN.md §5.1/§5.2/§9.4
("Doğrudan google.genai / groq çağırma; LLMRouter.route(...) üstünden git").

Tüm sağlayıcılar OpenAI-uyumlu `/chat/completions` arayüzü üzerinden
çağrılır (Gemini ve Groq ve DeepSeek'in hepsi bunu destekler); böylece
`openai` paketinin dışında ek bir SDK bağımlılığına gerek kalmaz. Model
adı asla çağıran kodda hard-code edilmez; her zaman bu router üzerinden
seçilir.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Protocol

from legalai.packages.shared.settings import settings
from legalai.packages.shared.tenant import current_tenant
from legalai.packages.usage.store import UsageStore
from legalai.packages.pii.outbound import mask_for_external

Task = Literal["simple", "reasoning"]


class LLMNotConfiguredError(RuntimeError):
    """`task` için uygun hiçbir sağlayıcının API anahtarı `.env`'de yoksa fırlatılır."""


class LLMClient(Protocol):
    provider: str
    model: str

    async def generate(self, system: str, user: str) -> str: ...


@dataclass(frozen=True)
class _ProviderSpec:
    provider: str
    base_url: str
    model: str
    api_key: str


class _OpenAICompatibleClient:
    """Gemini/Groq/DeepSeek gibi OpenAI-uyumlu bir `base_url` sunan her
    sağlayıcı için ortak istemci."""

    def __init__(self, spec: _ProviderSpec) -> None:
        self._spec = spec
        self.provider = spec.provider
        self.model = spec.model

    async def generate(self, system: str, user: str) -> str:
        from openai import AsyncOpenAI

        system = await mask_for_external(system)
        user = await mask_for_external(user)
        client = AsyncOpenAI(api_key=self._spec.api_key, base_url=self._spec.base_url)
        response = await client.chat.completions.create(
            model=self._spec.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        await self._record_usage(response)
        return response.choices[0].message.content or ""

    async def _record_usage(self, response: Any) -> None:
        usage = getattr(response, "usage", None)
        if usage is None:
            return
        input_tokens = _usage_value(usage, "prompt_tokens", "input_tokens")
        output_tokens = _usage_value(usage, "completion_tokens", "output_tokens")
        if input_tokens is None or output_tokens is None:
            return
        try:
            tenant_id = current_tenant().tenant_id
            await UsageStore().record(
                tenant_id=tenant_id,
                model=self.model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd_estimate=estimate_usage_cost(self.model, input_tokens, output_tokens),
            )
        except Exception:
            # Usage accounting must not turn an otherwise valid legal answer into
            # a failed request. The report remains an estimate, not billing truth.
            return


_MODEL_RATES_USD_PER_MILLION: dict[str, tuple[float, float]] = {
    "gemini-2.0-flash": (0.10, 0.40),
    "gemini-2.5-pro": (1.25, 5.00),
    "deepseek-reasoner": (0.55, 2.19),
    "llama-3.3-70b-versatile": (0.59, 0.79),
    "openai/gpt-4o-mini": (0.15, 0.60),
}


def _usage_value(usage: Any, *names: str) -> int | None:
    for name in names:
        value = usage.get(name) if isinstance(usage, dict) else getattr(usage, name, None)
        if value is not None:
            return int(value)
    return None


def estimate_usage_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    input_rate, output_rate = _MODEL_RATES_USD_PER_MILLION.get(model, (0.0, 0.0))
    return (input_tokens * input_rate + output_tokens * output_rate) / 1_000_000


# (provider, base_url, model, settings alan adı) — sırayla denenir, ilk
# API anahtarı ayarlı olan sağlayıcı seçilir.
_SIMPLE_CANDIDATES: list[tuple[str, str, str, str, str]] = [
    ("groq", "https://api.groq.com/openai/v1", "llama-3.3-70b-versatile", "groq_api_key", "groq_model"),
    (
        "gemini",
        "https://generativelanguage.googleapis.com/v1beta/openai/",
        "gemini-2.0-flash",
        "gemini_api_key",
        "gemini_model",
    ),
    (
        "openrouter",
        "https://openrouter.ai/api/v1",
        "openai/gpt-4o-mini",
        "openrouter_api_key",
        "openrouter_model",
    ),
]
_REASONING_CANDIDATES: list[tuple[str, str, str, str, str]] = [
    (
        "gemini",
        "https://generativelanguage.googleapis.com/v1beta/openai/",
        "gemini-2.5-pro",
        "gemini_api_key",
        "gemini_model",
    ),
    (
        "deepseek",
        "https://api.deepseek.com/v1",
        "deepseek-reasoner",
        "deepseek_api_key",
        "deepseek_model",
    ),
    ("groq", "https://api.groq.com/openai/v1", "llama-3.3-70b-versatile", "groq_api_key", "groq_model"),
    (
        "openrouter",
        "https://openrouter.ai/api/v1",
        "openai/gpt-4o-mini",
        "openrouter_api_key",
        "openrouter_model",
    ),
]


class LLMRouter:
    """`route("simple")` hızlı/ucuz modeli, `route("reasoning")` derin
    araştırma/analiz için daha güçlü bir modeli döner. Hangi sağlayıcının
    seçildiği, `.env`'de HANGİ anahtarların dolu olduğuna bağlıdır — kod
    içinde asla sabit bir sağlayıcıya bağlanılmaz."""

    def __init__(self, client_factory: type[_OpenAICompatibleClient] = _OpenAICompatibleClient) -> None:
        self._client_factory = client_factory

    def route(self, task: Task = "simple", provider: str | None = None) -> LLMClient:
        selected_provider = provider or getattr(settings, "legalai_llm_provider", "auto")
        candidates = _REASONING_CANDIDATES if task == "reasoning" else _SIMPLE_CANDIDATES
        if selected_provider != "auto":
            candidates = [candidate for candidate in candidates if candidate[0] == selected_provider]
            if not candidates:
                raise LLMNotConfiguredError(
                    f"Desteklenmeyen LLM sağlayıcısı: {selected_provider}. "
                    "LEGALAI_LLM_PROVIDER için auto, gemini, openrouter, deepseek veya groq kullanın."
                )
        for provider_name, base_url, default_model, key_attr, model_attr in candidates:
            api_key = getattr(settings, key_attr, "")
            if api_key:
                model = getattr(settings, model_attr, "") or default_model
                if (
                    task == "reasoning"
                    and provider_name == "gemini"
                    and model == "gemini-2.0-flash"
                ):
                    model = default_model
                spec = _ProviderSpec(
                    provider=provider_name,
                    base_url=base_url,
                    model=model,
                    api_key=api_key,
                )
                return self._client_factory(spec)
        if selected_provider != "auto":
            key_name = {
                "gemini": "GEMINI_API_KEY",
                "openrouter": "OPENROUTER_API_KEY",
                "deepseek": "DEEPSEEK_API_KEY",
                "groq": "GROQ_API_KEY",
            }.get(selected_provider, f"{selected_provider.upper()}_API_KEY")
            raise LLMNotConfiguredError(f"Seçilen sağlayıcı yapılandırılmadı; {key_name} eksik.")
        raise LLMNotConfiguredError(
            "Hiçbir LLM sağlayıcısı için API anahtarı bulunamadı. "
            ".env dosyasına GEMINI_API_KEY, GROQ_API_KEY, OPENROUTER_API_KEY veya DEEPSEEK_API_KEY girin "
            "(bkz. FORK-KAPSAMLI-PLAN.md §1.10.A-F)."
        )


llm_router = LLMRouter()
