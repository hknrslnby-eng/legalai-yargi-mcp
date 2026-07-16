"""Uygulama ayarları — 12-factor config.
Bkz. FORK-KAPSAMLI-PLAN.md §2.4. Kod içinde asla `os.environ["..."]`
kullanılmaz; her zaman `settings.xxx` üstünden gidilir."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    tenant_id: str = "local"
    tenant_name: str = "Local"
    database_url: str = "sqlite+aiosqlite:///./.data/legalai.db"
    storage_root: str = "./.data"
    usage_db_path: str = "./.data/usage.db"

    gemini_api_key: str = ""
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    deepseek_api_key: str = ""
    groq_api_key: str = ""
    openrouter_api_key: str = ""
    huggingface_token: str = ""

    # LLMRouter sağlayıcı seçimi: auto, anahtarı bulunan sağlayıcılar içinde
    # görev türüne göre varsayılan sırayı kullanır; diğer değerler açık seçimdir.
    legalai_llm_provider: str = "auto"
    gemini_model: str = "gemini-2.0-flash"
    groq_model: str = "llama-3.3-70b-versatile"
    openrouter_model: str = "openai/gpt-4o-mini"
    deepseek_model: str = "deepseek-reasoner"

    enable_aggressive_opposing: bool = True
    enable_deep_research: bool = True
    enable_auth: bool = False

    # PII gateway envelope encryption — bkz. FORK-KAPSAMLI-PLAN.md Hafta 6.
    # Boşsa gateway ilk kullanımda rastgele bir KEK üretir ve UYARIR;
    # üretimde/kalıcı ortamlarda MUTLAKA .env'e sabit bir değer yazılmalı,
    # aksi halde yeniden başlatmada eski maskelenmiş veriler açılamaz.
    pii_kek_base64: str = ""
    pii_map_db_path: str = "./.data/pii_map.db"


settings = Settings()
