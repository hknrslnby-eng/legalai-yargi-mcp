# v0.2.5 Sürüm Hizalaması ve IDE Kurulum Matrisi Tasarımı

## Amaç

SocratLegal v0.2.5 sürümünü, uygulamanın iç sürüm bilgisi, Python paket metadata'sı, portable manifesti, release tag'i ve kullanıcı belgeleri birbiriyle tutarlı olacak şekilde yayımlamak; ayrıca desteklenen IDE kurulumlarının temiz geçici ortamlarda otomatik doğrulanmasını sağlamak.

## Mevcut bulgu ve kök neden

v0.2.4 portable paketinde Codex MCP sağlık kontrolü başarıyla çalışmış, ancak sonuç `version: "0.2.3"` döndürmüştür. `origin/main` içindeki `pyproject.toml`, `legalai/__init__.py`, MCP sunucusu, API ve CLI sürüm değerleri birbirinden bağımsız sabitler olarak tutulmaktadır. Portable paketleme script'i release tag sürümünü yalnızca arşiv adı ve manifest için kullanmakta, uygulama içindeki sabitleri değiştirmemektedir.

Bu nedenle çözüm yalnızca arşiv adını değiştirmek değil, sürüm değerlerinin kaynağını tekleştirmek ve release workflow'unda tag ile kaynak sürümünü karşılaştırmaktır.

## Tasarım kararları

### 1. Tek sürüm kaynağı

`legalai.__version__` uygulamanın tek sürüm kaynağı olacaktır. `pyproject.toml` setuptools dynamic version yapılandırmasıyla bu değeri okuyacaktır. MCP sunucusu, FastAPI uygulaması ve CLI varsayılanları aynı değeri import edecektir.

v0.2.5 dalında beklenen değer `0.2.5` olacaktır. Kod içindeki bağımsız `0.2.3` ve önceki sürüm sabitleri kaldırılacaktır. Tarihsel demo metinleri dışında güncel kullanıcıya gösterilen sürüm ve release bağlantıları v0.2.5'e hizalanacaktır.

### 2. Sürüm/tag doğrulaması

`scripts/check_release_version.py` tag değerini ve `legalai.__version__` değerini karşılaştıracaktır. Tag `v0.2.5`, kaynak sürüm `0.2.5` biçimine dönüştürülerek karşılaştırılacaktır. Eşleşme yoksa script sıfırdan farklı kodla sonlanacaktır.

Portable release workflow'u paketleme adımından önce bu kontrolü çalıştıracaktır. Böylece yanlış sürümle release asset'i üretilmeyecektir.

### 3. IDE kurulum matrisi

Geçici bir kullanıcı ve proje dizini altında aşağıdaki beş desteklenen IDE ayrı ayrı kurulacaktır:

- Cursor: genel JSON `mcpServers` şeması
- Antigravity: genel JSON `mcpServers` şeması
- VS Code: workspace `.vscode/mcp.json` içindeki `servers` şeması
- Claude Desktop: genel JSON `mcpServers` şeması
- Codex: TOML `mcp_servers` şeması

Testler her IDE için doğru dosya biçimini, `socratlegal` kaydını, portable komutunu, `app` çalışma dizinini, mevcut başka server kayıtlarının korunmasını ve ikinci kurulumda idempotent sonucu kontrol edecektir. Bir IDE seçildiğinde diğer IDE dosyalarının oluşturulmaması da doğrulanacaktır.

Bu testler IDE uygulamalarının GUI davranışını değil, installer'ın ürettiği MCP sözleşmesini doğrular. Gerçek host doğrulaması için Codex portable ve VS Code kaynak kurulumu ayrıca yapılacaktır.

### 4. Release workflow doğrulaması

Release workflow'u v0.2.5 için şu sırayı izleyecektir:

1. Python/uv çalışma ortamını kurmak.
2. Kaynak sürüm ile tag sürümünü karşılaştırmak.
3. Installer ve packaging testlerini çalıştırmak.
4. Portable ağacını oluşturmak.
5. Portable ağacının sürümünü ve beklenen launcher/runtime dosyalarını kontrol etmek.
6. ZIP, checksum ve manifest asset'lerini üretmek.
7. GitHub Release'e asset'leri yüklemek.

Test veya sürüm kontrolü başarısız olursa release asset'i oluşturulmayacaktır.

### 5. v0.2.4 politikası

Mevcut `v0.2.4` tag'i ve release'i geriye dönük olarak yeniden yazılmayacaktır. v0.2.5 güncel ve önerilen release olacaktır. v0.2.4'ün silinmesi veya release gövdesinin değiştirilmesi bu çalışmanın zorunlu parçası değildir ve ayrıca açık kullanıcı onayı gerektirir.

## Kapsam dışı

- v0.2.5 için macOS veya Linux portable asset'i üretmek.
- Cursor veya Antigravity kullanıcısının mevcut ayarlarını değiştirmek.
- API sağlayıcılarının veya hukuk muhakeme katmanlarının davranışını değiştirmek.
- v0.2.4 tag'ini force-push ile yeniden yazmak.

## Kabul ölçütleri

- `legalai.__version__`, Python package metadata'sı, MCP sağlık kontrolü, API ve CLI aynı `0.2.5` değerini gösterir.
- Tag/source mismatch testi yanlış değerle başarısız, doğru değerle başarılı olur.
- Beş IDE installer testinin tamamı geçer; mevcut başka MCP kayıtları korunur.
- Portable root regression testi geçer.
- Packaging testi runtime'ı içerir ve kullanıcı state'ini dışarıda bırakır.
- Release workflow'u v0.2.5 tag'inde yeşil tamamlanır ve Windows x64 ZIP/checksum/manifest üretir.
- v0.2.5 portable Codex sağlık kontrolü `status: "ok"`, `version: "0.2.5"`, `external_calls: false` döndürür.
- VS Code kaynak kurulumu temiz bir worktree'de `.vscode/mcp.json` üzerinden doğrulanır.

