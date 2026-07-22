# LegalAI paket alanı

Bu klasör, SocratLegal fork'unda eklenen hukuk katmanlarını içerir. Son kullanıcı kurulumu, yeteneklerin sade açıklaması, API anahtarı kullanımı ve desteklenen IDE'ler için [kök README](../README.md) dosyasına bakın.

Kaynak kodla çalışanlar için temel komutlar:

```powershell
uv sync --frozen --dev
uv run socratlegal-mcp
uv run socratlegal qa "Hukuki soruyu kaynaklı ve ihtimalli analiz et"
```

Tüm çıktılar analysis-only ve non-binding araştırma taslağıdır. Upstream MIT lisansı ve fork atıfları [LICENSE](../LICENSE) ile [NOTICE.md](../NOTICE.md) içinde açıklanır.
