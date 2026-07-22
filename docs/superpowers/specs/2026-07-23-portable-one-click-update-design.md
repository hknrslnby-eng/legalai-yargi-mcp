# Portable Tek Tıklamalı Güncelleme Tasarımı

## Amaç

Windows x64 portable kullanıcılarının her sürümde GitHub Releases sayfasından ZIP aramasına gerek kalmadan, portable klasöründeki bir `update.cmd` dosyasına çift tıklayarak güvenli güncelleme yapabilmesi.

## Kapsam

- Portable paket köküne `update.cmd` eklenir.
- `.cmd` dosyası, portable paketin kendi `runtime\\uv.exe` çalıştırıcısıyla yeni CLI komutunu başlatır.
- CLI manifesti HTTPS üzerinden okur, yeni sürüm olup olmadığını kontrol eder ve kullanıcı onayından sonra arşivi indirir.
- İndirilen arşivin dosya adı ve SHA-256 değeri manifest ile doğrulanmadan aktif uygulama değiştirilmez.
- Mevcut `apply_update` akışı kullanılır; yalnızca `app` değiştirilir, `config`, `data`, API anahtarları, belgeler ve yerel corpus korunur.
- Güncelleme başarısız olursa `app.previous` üzerinden mevcut geri dönüş davranışı korunur.

## Kullanıcı akışı

1. Kullanıcı IDE'leri ve SocratLegal sunucusunu kapatır.
2. Portable klasöründeki `update.cmd` dosyasına çift tıklar.
3. Program mevcut sürümü, yeni sürümü ve release adresini gösterir.
4. Kullanıcı açıkça onaylarsa manifest indirilir veya doğrulanır, arşiv geçici klasöre indirilir ve checksum kontrol edilir.
5. Uygulama güncellenir; kullanıcı ayarları ve verileri yerinde kalır.
6. Kullanıcı IDE'leri yeniden başlatır.

Kullanıcı onaylamazsa veya yeni sürüm yoksa dosya sistemi değişmez. Sessiz, izinsiz ve arka planda otomatik kurulum yapılmaz.

## Bileşen sınırları

- `scripts/update.cmd`: yalnızca portable kökü bulur, `SOCRATLEGAL_ENV_FILE` ayarını taşır ve CLI güncelleme komutunu çağırır.
- `legalai/packages/installer/update.py`: manifest, güvenli HTTPS indirme, geçici dosya, arşiv adı, boyut/checksum ve mevcut atomik uygulama değiştirme akışını yönetir.
- `legalai/apps/cli/main.py`: kullanıcı onayı, çıktı ve hata mesajlarını yönetir; iş mantığını tekrar etmez.
- `scripts/package_portable.py`: `update.cmd` dosyasını ZIP köküne taşır.

## Güvenlik ve hata davranışı

- Manifest ve arşiv URL'leri HTTPS olmalıdır.
- Manifestteki release URL'sinden beklenen GitHub arşiv adresi türetilir; kullanıcıdan keyfi URL ile indirme varsayılan akışa girmez.
- Arşiv yalnızca geçici klasöre indirilir; checksum uyuşmazlığında aktif uygulama değişmez.
- Ağ hatası, bozuk JSON, geçersiz sürüm, desteklenmeyen arşiv veya disk hatası anlaşılır bir hata olarak gösterilir.
- Kullanıcı verileri ve `.env` hiçbir güncelleme arşivinden okunup dışarı gönderilmez.
- İndirme için sınırsız bellek kullanımı yerine dosyaya akışlı yazma ve makul boyut sınırı uygulanır.

## Test kapsamı

- Manifestten arşiv URL'si türetme ve HTTPS kısıtı.
- İndirme başarısızlığı ve checksum uyuşmazlığında aktif uygulamanın değişmemesi.
- Onay verilmediğinde indirme ve dosya değişikliği yapılmaması.
- Başarılı güncellemede `config`, `data`, `.env` ve corpus dosyalarının korunması.
- `update.cmd` dosyasının portable paket kökünde bulunması ve `package_portable.py` tarafından arşive alınması.
- Mevcut update/check/apply/rollback testlerinin geriye dönük çalışması.
