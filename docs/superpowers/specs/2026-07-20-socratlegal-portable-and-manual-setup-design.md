# SocratLegal Portable Paket ve Manuel MCP Kurulum Tasarımı

## Durum

Taslak tasarım — uygulama koduna geçmeden önce kullanıcı incelemesi gerekir.

## Amaç

SocratLegal'i hosting gerektirmeden, Python veya sistem genelinde kurulu `uv`
zorunluluğunu son kullanıcıdan mümkün olduğunca kaldırarak IDE'lerde
kurulabilir hale getirmek. Aynı zamanda teknik kullanıcıların doğrudan manuel
MCP JSON/TOML kaydıyla kurulum yapabilmesini ve bu yolun README'de açık,
doğrulanabilir ve hata önleyici biçimde belgelenmesini sürdürmek.

Bu tasarım SocratLegal'in yerel `stdio` çalışma modelini korur. GitHub yalnızca
kaynak kodu ve portable dağıtım arşivlerini dağıtım kanalı olarak kullanır;
çalışma zamanında uzak SocratLegal hosting servisi varsayılmaz.

## Kapsam dışı

- Bu aşamada tek dosyalık Windows/macOS/Linux executable üretimi.
- Yeni bir uzak MCP hosting servisi veya özel domain.
- Upstream modüllerinin sözleşmelerini değiştirmek.
- Mevcut Cursor, Antigravity veya diğer kullanıcı ayarlarını otomatik olarak
  bu çalışma sırasında değiştirmek.

Executable seçeneği ileride portable paketin üzerine eklenebilecek ayrı bir
dağıtım biçimidir.

## Kullanıcı profilleri

### Normal kullanıcı — portable paket

Kullanıcı, işletim sistemine uygun bir Release arşivini indirir ve çıkarır.
Arşiv içindeki kurulum yardımcısını çalıştırır. Yardımcı, seçilen IDE'leri
algılar, mevcut ayarları parse eder, SocratLegal kaydını güvenli biçimde
birleştirir ve sağlık kontrolü yapar.

Kullanıcının sisteminde Python veya `uv` bulunması beklenmez. Portable pakette
platforma uygun `uv` çalıştırıcısı ve SocratLegal proje dosyaları bulunur;
`uv`, gerekli Python sürümünü ve bağımlılık ortamını kendi yönetir.

### Geliştirici veya ileri kullanıcı — manuel JSON/TOML

Kullanıcı mevcut proje checkout'ını kullanır ve IDE'nin yerel MCP ayarına
SocratLegal `stdio` kaydını kendisi ekler. README, her IDE için doğru dosya
konumunu, `command`, `args`, `cwd` alanlarını ve Windows path kaçışlarını
tam örneklerle açıklar.

Manuel yol, portable kurulumdan bağımsız olarak korunur. Kullanıcı kendi
hedef dizinini seçtiğinde README'deki örnekteki proje yolu kendi gerçek yolu
ile değiştirilir; GitHub deposu URL'si `url` alanına MCP endpoint'i gibi
yazılmaz.

## Dağıtım biçimi

İlk portable sürüm tek bir executable değil, platforma göre arşivlenmiş bir
paket olur:

```text
SocratLegal-Windows-x64.zip
SocratLegal-macos-arm64.tar.gz
SocratLegal-macos-x64.tar.gz
SocratLegal-linux-x64.tar.gz
```

Arşiv içeriği mantıksal olarak şu bileşenleri taşır:

```text
SocratLegal/
  app/                  # SocratLegal kaynak/dağıtım dosyaları
  runtime/              # platforma uygun uv çalıştırıcısı
  data/                 # yerel corpus ve çalışma verileri için ayrılmış alan
  install.ps1 veya install.sh
  start.cmd veya start.sh
  README.txt
  CHECKSUMS.txt
```

Kurulum sırasında yazılabilir bir kullanıcı dizini tercih edilir. Varsayılan
hedef platforma göre `%LOCALAPPDATA%/SocratLegal` veya kullanıcı home dizini
altında bir SocratLegal klasörüdür. Program dosyaları ile corpus/veri dizini
ayrılabilir; kullanıcı isterse hedef veri dizinini seçebilir.

## Kurulum yardımcısı davranışı

Kurulum yardımcısı aşağıdaki adımları izler:

1. İşletim sistemi ve mimariyi doğrular.
2. Portable paketin bütünlüğünü ve beklenen dosyaları kontrol eder.
3. Kullanıcıdan kurulum ve isteğe bağlı veri dizinini alır.
4. Cursor, Codex, Antigravity, VS Code ve Claude Desktop kurulumlarını tespit
   eder.
5. Kullanıcıya hangi IDE'lerin yapılandırılacağını seçtirir.
6. Her istemcinin ayar dosyasını JSON veya TOML olarak parse eder.
7. Mevcut sunucu kayıtlarını koruyarak yalnızca `socratlegal` kaydını ekler
   veya günceller.
8. Değişiklikten önce timestamp'li yedek oluşturur.
9. Dosyayı tekrar parse ederek sözdizimi doğrulaması yapar.
10. Yerel SocratLegal sağlık kontrolünü ve MCP araç keşfini çalıştırır.
11. Sonuçları normal kullanıcı dilinde gösterir.

Kurulum yardımcısı hiçbir zaman mevcut yapılandırmanın sonuna ikinci bir
bağımsız JSON nesnesi eklememelidir. JSON birleştirme işlemi yapılandırma
nesnesi seviyesinde yapılmalıdır.

## IDE kayıt stratejisi

Her IDE için ayrı bir adapter/serializer bulunur. Ortak iç model:

```text
server_name = socratlegal
transport = stdio
executable = portable runtime veya yerel python/uv
arguments = server başlatma argümanları
working_directory = SocratLegal app dizini
```

İstemciye göre dışa aktarım:

- Cursor ve Claude: `mcpServers` JSON nesnesi.
- Antigravity: `mcpServers` JSON nesnesi.
- VS Code: `servers` altında `type = stdio` JSON nesnesi.
- Codex: `[mcp_servers.socratlegal]` TOML bölümü.

Kurulum yardımcısı IDE'nin desteklemediği veya bulunamadığı durumda bunu
başarısızlık gibi gizlememeli; “bulunamadı / manuel kurulum gerekir” şeklinde
raporlamalıdır.

## Manuel kurulum dokümantasyonu

README ve ayrı bir kullanıcı kılavuzu şu bilgileri içermelidir:

- Hosting olmadan yerel `stdio` kurulumunun ne anlama geldiği.
- GitHub repo URL'sinin neden `url` alanına yazılmayacağı.
- Python/uv kullanan yerel checkout yöntemi.
- Portable paket yöntemi.
- Cursor, Codex, Antigravity, VS Code ve Claude için ayrı dosya konumları.
- Windows path'lerinde çift ters bölü çizgi kullanımı.
- JSON'da yalnızca tek dış nesne bulunması gerektiği.
- Mevcut MCP kayıtlarının korunarak aynı `mcpServers` nesnesi altında
  birleştirilmesi.
- Kurulum sonrası `socratlegal_saglik_kontrolu` ve `socratlegal_yardim`
  testleri.
- `uv` veya Python bulunamadığında anlaşılır hata ve çözüm.
- Portable paketin checksum doğrulaması.
- Yerel corpus dizini ve kişisel verilerin dış servise gönderilmeden önce
  maskelenmesi.

README örnekleri, sabit kullanıcı adı veya sabit masaüstü yolu yerine
`<SOCRATLEGAL_DIZINI>` gibi açık placeholder kullanmalı; örneğin nasıl
değiştirileceğini hemen altında göstermelidir.

## Güncelleme ve veri güvenliği

- Release arşivleri GitHub Release üzerinden yayımlanır.
- Her arşiv için checksum yayımlanır.
- Güncelleme uygulama dosyalarını yenilerken yerel `data`/corpus dizinini
  silmez.
- Ayar dosyasının yedeği alınmadan güncelleme yapılmaz.
- Kullanıcının raporları veya corpus belgeleri GitHub'a otomatik gönderilmez.
- Canlı resmi kaynak sorgularında mevcut PII maskeleme sınırı korunur.
- Kurulum yardımcısı API anahtarlarını loglamaz.

## Test kabul kriterleri

### Paket testi

- Temiz Windows ortamında sistem Python'u olmadan paket açılabilmeli.
- Sistem genelinde `uv` olmadan portable runtime çalışabilmeli.
- SocratLegal MCP süreci `tools/list` yanıtı verebilmeli.
- `socratlegal_saglik_kontrolu` `status = ok` döndürmeli.
- Yerel corpus dizini oluşturulmalı veya mevcutsa korunmalı.

### Yapılandırma testi

- Boş Cursor/Antigravity/VS Code/Claude/Codex ayarına ekleme yapılabilmeli.
- Mevcut sunucuların bulunduğu ayara ekleme yapılabilmeli.
- Aynı kurulum iki kez çalıştırıldığında duplicate kayıt oluşmamalı.
- Geçersiz JSON/TOML durumunda dosya bozulmamalı ve yedekten geri dönülebilmeli.
- Windows yollarındaki boşluklar çalışmalı.

### Manuel dokümantasyon testi

- Yazılım bilmeyen bir kullanıcı yalnızca README'yi izleyerek kurulum
  yapabilmeli.
- Her örnekteki sabit yolun nasıl değiştirileceği açıkça belirtilmeli.
- Kurulum sonrası ilk sağlık kontrolü ve basit katmanlı analiz çalışmalı.

## Uygulama sırası

1. Ortak kurulum modeli ve path/IDE adapter sözleşmeleri.
2. Güvenli JSON/TOML merge ve yedekleme kütüphanesi.
3. Portable runtime paketleme akışı.
4. Windows `install.ps1`; ardından macOS/Linux scriptleri.
5. Sağlık ve duplicate-kayıt testleri.
6. README ve kullanıcı kurulum kılavuzu.
7. GitHub Release artifact üretimi.
8. İsteğe bağlı tek dosyalık executable araştırması.

Bu aşamaların hiçbiri upstream repo dosyalarını veya upstream public API
sözleşmelerini değiştirmez.
