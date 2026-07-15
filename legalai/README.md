# legalai/

Yargı-MCP fork'unun üzerine inşa edilen ürün katmanı. Upstream kodu
(fork kökündeki `*_mcp_module/`, `mcp_server_main.py` vb.) buraya
taşınmaz; bu klasör sadece bizim eklediğimiz kodu barındırır.

Ayrıntılı mimari için bkz. `../FORK-KAPSAMLI-PLAN.md`.

## Klasörler

- `packages/` — paylaşılan kütüphane kodu (katmanlar, jurisdiction profilleri, PII, AİHM, LLM router, storage, shared)
- `apps/` — çalıştırılabilir uygulamalar (CLI, API, MCP)
- `infra/` — docker ve migration dosyaları
- `configs/` — YAML tabanlı yargı türü profilleri
- `docs/` — proje dokümantasyonu
- `tests/` — testler
