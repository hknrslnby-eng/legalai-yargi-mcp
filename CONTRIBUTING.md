# LegalAI'ye katkı

LegalAI, Yargı MCP fork'u üzerine geliştirilen yerel ve çok istemcili bir MCP projesidir. Katkılar mevcut Cursor, Codex, Claude, Antigravity ve VS Code kurulumlarını bozmamalıdır.

## Yerel kurulum

Python 3.11 veya üzeri ve `uv` kurulu olmalıdır:

```powershell
uv venv --python 3.12
uv sync --frozen --dev
```

MCP sunucusunu ayrı hosting olmadan çalıştırmak için:

```powershell
uv run legalai-mcp
```

IDE ayarlarında mevcut kullanıcıya özel dosyaları silmeyin veya yeniden adlandırmayın. Secretları `.env` içinde tutun; Git'e eklemeyin.

## Test

Değişiklikten önce hedefli testi, değişiklikten sonra iki çalışma yolunu çalıştırın:

```powershell
uv run --no-cache pytest legalai/tests/apps -q
.venv\Scripts\python.exe -m pytest -q
uv run --no-cache pytest -q
```

Üretim kodu değişiklikleri için önce davranışı gösteren failing test yazılır. Yeni bir MCP tool için hem FastMCP kaydı hem de doğrudan çağrılabilir Python facade test edilir.

## Gizlilik ve güvenlik

- Gerçek kişi adı, TCKN, adres, dosya numarası veya gizli belge commit etmeyin.
- API anahtarlarını Markdown, JSON, TOML veya Python dosyasına yazmayın.
- LegalAI'nin dış çağrı sınırında yerel PII maskelemesini kaldırmayın.
- Testlerde anonim veya açıkça sentetik veri kullanın.
- Kullanıcıya kesin/bağlayıcı hukukî sonuç vaat eden metin eklemeyin.

## Kod ve dokümantasyon ilkeleri

- Yerel IDE/MCP istemcileri ana kullanıcı yüzeyidir; CLI yardımcı yüzeydir.
- MCP tool açıklamaları yazılım bilmeyen kullanıcıya hangi durumda kullanılacağını anlatmalıdır.
- Çıktılarda kaynak künye, kısa alıntı, belirsizlik, varsayım ve eksik olgular korunmalıdır.
- Ayrı hosting, global daemon veya ortak port eklemeyin.
- Değişiklikleri küçük ve gözden geçirilebilir commitlere ayırın.

## Pull request kontrol listesi

- [ ] Failing test yazıldı ve kırmızı aşama görüldü.
- [ ] Hedefli test geçti.
- [ ] `.venv` ve `uv run` tam testleri geçti.
- [ ] `git diff --check` temiz.
- [ ] Secret veya kişisel veri eklenmedi.
- [ ] `.cursor/mcp.json`, `.codex/config.toml` ve kullanıcı ayarları gereksiz yere değiştirilmedi.
- [ ] README/demo/kurulum metni gerekiyorsa güncellendi.
- [ ] Çıktının `analysis_only` ve `non_binding` sınırları korunuyor.
