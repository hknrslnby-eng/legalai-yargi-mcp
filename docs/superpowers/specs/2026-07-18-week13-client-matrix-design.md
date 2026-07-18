# Week 13 Çoklu İstemci Uyumluluğu Tasarım Belgesi

## Amaç

LegalAI'nin Codex, Cursor, Claude, Antigravity ve VS Code gibi yerel MCP istemcilerinde aynı STDIO sunucusu ve aynı tool/resource sözleşmesiyle kullanılmasını belgelemek ve mevcut istemci ayarlarının bozulmadığını otomatik olarak doğrulamak.

## Tasarım kararı

İstemciye özel runtime kodu eklenmeyecek. Her istemci kendi MCP ayarından aynı proje komutunu çalıştıracak; LegalAI sunucusu istemciyi ayırt etmeye çalışmayacak.

Config dosyaları için test yalnızca okuma/parsing yapacak:

- `.codex/config.toml` TOML olarak okunur.
- `.cursor/mcp.json` JSON olarak okunur.
- `legalai` kaydının STDIO komutu ve secret içermediği kontrol edilir.
- Cursor'daki mevcut `yargi-mcp-fork` kaydının korunduğu kontrol edilir.
- Config dosyaları test sırasında yazılmaz.

## Kullanıcı akışı

Her istemcide aynı doğrulama sırası kullanılır:

1. Proje MCP ayarını aç.
2. `legalai` kaydını ekle veya mevcut kaydı yeniden yükle.
3. `legalai_saglik_kontrolu` çalıştır.
4. `legalai_yardim` ile yetenek kataloğunu aç.
5. Sohbet alanında doğal dilde soru sor.

İstemcilerin menü adları değişebilir. Dokümantasyon kesin UI konumu iddia etmeyecek; “MCP Tools/Servers/Settings” gibi istemcinin eşdeğer alanlarını kullanacaktır.

## Kapsam dışı

- Kullanıcının mevcut `.cursor/mcp.json` veya global IDE ayarlarını değiştirmek.
- Hosting, HTTP transport veya global daemon.
- IDE’leri otomatik kurmak veya kullanıcının hesabında oturum açmak.
- Week 14 jurisdiction persona promptlarının uygulanması.

## Kabul kriterleri

- Config smoke testleri mevcut Codex ve Cursor kayıtlarını bağımsız parse eder.
- Secret veya kullanıcıya özel yeni config değeri üretilmez.
- İstemci matrisi beş istemciyi, portable komutu, health-check’i, discovery’i ve troubleshooting akışını açıklar.
- MCP health-check, discovery tool, capabilities resource ve yönlendirilmiş promptların mevcut testleri yeşil kalır.
- `.venv` ve `uv run` full test suite’leri geçer.
