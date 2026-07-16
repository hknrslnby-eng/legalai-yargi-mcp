# Hafta 10 Tenant Izolasyonu ve Usage Raporlama Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** LegalAI'nin yerel ve ileride uzak ortamlarda tenant bağlamını async sorgular arasında izole etmesi ve LLM kullanımını tenant/model/ay bazında raporlaması.

**Architecture:** `TenantContext` mevcut `ContextVar` tabanını korur; yeni scope yardımcıları token ile önceki tenant'ı geri yükler. `UsageStore` ayrı SQLite dosyasında append-only kayıtlar tutar. OpenAI-uyumlu LLM istemcisi provider response usage alanını best-effort olarak kaydeder; rapor CLI aynı store'u okur. Kullanım kaydı hatası hukuki analiz cevabını başarısız kılmaz ve raporda belirsizlik olarak gösterilir.

**Tech Stack:** Python 3.11+, `contextvars`, `aiosqlite`, Pydantic Settings, Typer, pytest/pytest-asyncio, mevcut LLMRouter.

## Global Constraints

- Ayrı hosting, global daemon veya ortak TCP portu eklenmeyecek.
- Python/uv uyumluluğu korunacak; `uv run` ve `.venv` Python aynı testleri çalıştıracak.
- Mevcut `.cursor/mcp.json` ve kullanıcıya özel ayarlar değiştirilmeyecek.
- Kamuya açık AIHM cache'i shared kalabilir; PII ve usage kayıtlarında `tenant_id` zorunludur.
- Maliyet alanı tahmindir; bağlayıcı faturalama veya resmi ücret beyanı değildir.
- Her üretim kodu değişikliğinden önce davranışı gösteren failing test yazılacak.

---

### Task 1: Async tenant scope izolasyonu

**Files:**
- Modify: `legalai/packages/shared/tenant.py`
- Create: `legalai/tests/shared/__init__.py`
- Create: `legalai/tests/shared/test_tenant.py`

**Interfaces:** `tenant_scope(ctx: TenantContext)` context manager'ı scope sonunda önceki tenant'ı geri yükler; mevcut `set_tenant(ctx)` çağrıları geriye uyumlu kalır.

- [ ] Failing test: iki tenant altında paralel 50 coroutine çalıştır ve her coroutine'in yalnız kendi tenant'ını gördüğünü doğrula; scope sonrasında başlangıç tenant'ının geri geldiğini doğrula.
- [ ] Testi çalıştır: `pytest legalai/tests/shared/test_tenant.py -q`; yeni yardımcı olmadığı için FAIL.
- [ ] Minimal implementation: `ContextVar.set()` token'ını kullanan `@contextmanager tenant_scope` ekle; `set_tenant` davranışını bozma.
- [ ] Testi çalıştır: aynı komut PASS.
- [ ] Commit: `feat: add async tenant scope isolation`.

### Task 2: Usage store ve aylık rapor sözleşmesi

**Files:**
- Modify: `legalai/packages/shared/settings.py`
- Create: `legalai/packages/usage/__init__.py`
- Create: `legalai/packages/usage/store.py`
- Create: `legalai/tests/usage/__init__.py`
- Create: `legalai/tests/usage/test_store.py`

**Interfaces:** `UsageStore.record(...)`, `UsageStore.report(month, tenant_id=None)`; rapor `calls`, `input_tokens`, `output_tokens`, `cost_usd_estimate` ve `by_model` alanlarını taşır.

- [ ] Failing test: iki tenant ve iki ay için kayıt ekle; tenant/ay filtresinin doğru toplamları döndürdüğünü doğrula.
- [ ] Testi çalıştır: `pytest legalai/tests/usage/test_store.py -q`; store yokluğu nedeniyle FAIL.
- [ ] Minimal implementation: tenant/model/token/maliyet/timestamp sütunları ve indeksleri olan SQLite schema; `YYYY-MM` doğrulaması; rapor sorguları.
- [ ] Testi çalıştır: aynı komut PASS.
- [ ] Commit: `feat: add tenant usage store and monthly report`.

### Task 3: LLM response usage instrumentation

**Files:**
- Modify: `legalai/packages/llm/router.py`
- Modify: `legalai/packages/shared/settings.py`
- Create: `legalai/tests/llm/test_usage_instrumentation.py`

**Interfaces:** `_OpenAICompatibleClient.generate` response usage alanından kayıt oluşturur; usage kaydı başarısız olursa model cevabı yine döner.

- [ ] Failing test: sahte OpenAI response'undan `prompt_tokens`/`completion_tokens` değerlerini alıp aktif tenant için UsageStore'a yazıldığını doğrula.
- [ ] Testi çalıştır: `pytest legalai/tests/llm/test_usage_instrumentation.py -q`; kayıt olmadığı için FAIL.
- [ ] Minimal implementation: response usage normalizer, model bazlı tahmini maliyet fonksiyonu ve best-effort recorder ekle; bilinmeyen modelde maliyeti 0 olarak işaretle.
- [ ] Testi çalıştır: aynı komut PASS.
- [ ] Commit: `feat: record llm usage by tenant`.

### Task 4: `legalai usage report` CLI

**Files:**
- Create: `legalai/apps/cli/main.py`
- Modify: `pyproject.toml`
- Create: `legalai/tests/cli/__init__.py`
- Create: `legalai/tests/cli/test_usage_cli.py`

**Interfaces:** `legalai usage report --month 2026-07 [--tenant-id ID]` JSON raporu stdout'a yazar; mevcut `legalai-mcp` entry point aynen kalır.

- [ ] Failing test: Typer runner ile ay raporu komutunun store raporunu JSON olarak verdiğini doğrula.
- [ ] Testi çalıştır: `pytest legalai/tests/cli/test_usage_cli.py -q`; entry point yokluğu nedeniyle FAIL.
- [ ] Minimal implementation: `usage` Typer group, `report` alt komutu ve `legalai` project script ekle.
- [ ] Testi çalıştır: aynı komut PASS; ayrıca `uv run --no-cache legalai usage report --help` çalışmalı.
- [ ] Commit: `feat: add legalai usage report cli`.

### Task 5: Stres testi ve roadmap dokümantasyonu

**Files:**
- Create: `legalai/tests/integration/test_week10_tenant_usage.py`
- Modify: `C:\Users\hakan\Desktop\Yargi MCP Fork\FORK-KAPSAMLI-PLAN.md` (repo dışı kaynak roadmap)

- [ ] Failing test: iki tenant altında 50'şer paralel iş çalıştır; PII tokenlarının tenantlar arasında çözülemediğini ve usage raporlarının ayrıştığını doğrula.
- [ ] Testi çalıştır: `pytest legalai/tests/integration/test_week10_tenant_usage.py -q`; scope/store entegrasyonu tamamlanmadığı için FAIL.
- [ ] Minimal implementation/test fixture: gerçek uzak API çağırmadan tenant scope + PII store + UsageStore zincirini çalıştır.
- [ ] Testi çalıştır: aynı komut PASS.
- [ ] Roadmap'e teknik bilirkişi raporu itiraz modülü için kapsam, sınırlar ve kabul kriterleri ekle; bu sprintte üretim kodu yazılmadığını açıkça belirt.
- [ ] Commit: `test: verify week 10 tenant isolation and usage reporting`.

### Task 6: Son doğrulama ve checkpoint

- [ ] `git diff --check` çalıştır.
- [ ] `.venv\\Scripts\\python.exe -m pytest -q` çalıştır; tüm testler PASS.
- [ ] `UV_CACHE_DIR=.uv-cache uv run --no-cache pytest -q` eşdeğerini Windows PowerShell'de çalıştır; tüm testler PASS.
- [ ] `uv run --no-cache legalai usage report --month 2026-07` smoke testini çalıştır.
- [ ] Kullanıcıya branch/commit kapsamını bildir; onayla birlikte GitHub push öner.

## Execution status

- [x] Tenant scope izolasyonu ve geri yükleme uygulandı.
- [x] Tenant/model/ay filtreli SQLite usage store uygulandı.
- [x] LLM response tokenları ve tahmini maliyet kaydı bağlandı; kayıt arızası cevap akışını kesmiyor.
- [x] `legalai usage report --month YYYY-MM [--tenant-id ID]` CLI'sı eklendi.
- [x] İki tenant altında 50'şer paralel iş ile PII/usage izolasyon testi geçti.
- [x] `.venv` ve `uv run` testleri: 158/158.
