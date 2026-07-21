# SocratLegal kullanıcı kurulumu

SocratLegal ayrı bir web sitesi, hosting veya sürekli açık bir sunucu gerektirmez. Kullanıcının bilgisayarında çalışan yerel STDIO MCP sunucusudur.

## Önerilen yol: portable paket

1. GitHub deposunun **Releases** sayfasından işletim sisteminize uygun ZIP veya `tar.gz` paketini indirin.
2. Paketi yazma izniniz olan bir klasöre çıkartın; örneğin Windows'ta `C:\Users\Siz\SocratLegal`.
3. Windows'ta `install.ps1`, macOS/Linux'ta `install.sh` dosyasını çalıştırın.
4. IDE'yi yeniden başlatın veya MCP sunucularını yeniden yükleyin.
5. Sohbete `SocratLegal sağlık kontrolü yap` yazın.

Portable pakette platforma uygun `uv` çalıştırıcısı bulunur. Bu nedenle sistemde ayrıca Python, uv veya GitHub CLI kurulması beklenmez. İlk çalıştırmada uv, `uv.lock` bağımlılıklarını kendi önbelleğine indirebilir; bu hosting kurulması değildir.

Windows örneği:

```powershell
.\install.ps1 -Ide cursor
```

Birden fazla istemci için:

```powershell
.\install.ps1 -Ide cursor -Ide codex -Ide antigravity
```

Kurulumdan önce ne yapılacağını görmek için `-DryRun`, ekrandaki iki bitişik JSON nesnesinden oluşan eski ayarı onarmayı denemek için `-Repair` kullanılır.

## Manuel checkout yolu

## Belge yüklendiğinde hangi yetenek kullanılır?

Tebligat, ihtar, dava dilekçesi, savunma talebi veya iddianame gibi süreci tetikleyen bir belge için sohbete “önce eksik bilgi-belge-delil listesini çıkar, sonra dava dışı ve dava içi çözüm yollarını süre ve merci riskleriyle karşılaştır” yazın. SocratLegal bunu `socratlegal_onbilgi_ve_strateji` yeteneğine yönlendirir. Tüm sonuçlar koşullu, analysis-only ve non-binding araştırma taslağıdır.

## Dilekçe üslup profili

Kullanıcı isterse kendi örnek dilekçelerinden yalnızca başlık, atıf biçimi, ton ve argüman sırası gibi yapısal sinyaller çıkarılabilir. Ham örnekler, kişisel veriler veya örnek metinler GPT/Claude/Codex genel eğitimine gönderilmez; profil yerel türetilmiş metadata'dır. Profilin bir işlemde uygulanması için `style_profile_consent=true` açık kullanıcı onayı gerekir. Profil temizlendiğinde türetilmiş yerel metadata da kaldırılmalıdır; hukuki kaynak ve güvenlik başlıkları üslup profili tarafından değiştirilemez.

Geliştirici veya kaynak koddan çalışan kullanıcı repoyu indirip sistemine `uv` kurduktan sonra şunları çalıştırabilir:

```powershell
uv sync --frozen --dev
uv run socratlegal install --install-dir "C:\SocratLegal" --ide cursor
```

Bu yol Python ve uv gerektirir; normal kullanıcı için portable paket tercih edilir. GitHub repo adresi bir MCP `url` endpoint'i değildir. Hosting kurulmadığı için IDE ayarında `url` yerine yerel `command`, `args` ve `cwd` kaydı kullanılır.

## Güncellemeler

Yeni özellikler yayınlandığında aynı portable paketin yeni sürümü indirilir. Uygulama güncellemesi `data` klasörünü, yerel corpus'u, belgeleri ve API anahtarlarını paketten silmez. Yeni sürüm önce geçici alanda açılır, SHA-256 doğrulanır, sonra `app.previous` yedeği bırakılarak devreye alınır. Başlangıç kontrolü başarısız olursa önceki sürüme dönülür.

Güncelleme kontrolü yalnızca sürüm metadata'sını okur ve varsayılan olarak 24 saatte bir yapılır; kullanıcı belgelerinin metni gönderilmez.

Yeni kurulumlarda ayrı bir manifest indirmeden GitHub Releases metadata'sı kontrol edilebilir:

```powershell
.\runtime\uv.exe run --directory .\app socratlegal update check --platform-tag windows-x64
```

Bu komut yalnızca yeni sürüm olup olmadığını ve ilgili release bağlantısını gösterir. Arşiv otomatik olarak indirilmez veya kurulmaz. Kullanıcı yeni portable paketi Releases sayfasından açıkça indirip checksum'ı doğruladıktan sonra `update apply` komutunu çalıştırır. İnternet erişimi istenmiyorsa mevcut `--manifest-file` seçeneğiyle yerel metadata kullanılabilir.

```powershell
.\runtime\uv.exe run --directory .\app socratlegal update check --manifest-file .\release-manifest-windows-x64.json
.\runtime\uv.exe run --directory .\app socratlegal update apply --archive .\socratlegal-NEW-windows-x64.zip --manifest-file .\release-manifest-windows-x64.json --active-app .\app
.\runtime\uv.exe run --directory .\app socratlegal update rollback --active-app .\app
```

Güncelleme sırasında IDE JSON/TOML dosyaları yeniden yazılmaz; IDE'deki MCP kaydı aynı kalır.

## Kullanıcı hangi özelliği seçer?

Araç adlarını ezberlemek gerekmez. Sohbete doğal dille isteğinizi yazabilirsiniz:

- “Bu soruyu yürürlük ve olay tarihlerini ayırarak katmanlı analiz et.”
- “Karşı tarafın en güçlü karşı argümanlarını ve karşıt içtihatları getir.”
- “Dava, icra, arabuluculuk, idareye başvuru, 35/A ve sulh seçeneklerini birlikte değerlendir.”
- “Yüklediğim bilirkişi raporunu teknik ve hukuki yönden incele; itiraz dilekçesi taslağı hazırla.”
- “Bu uyuşmazlık hakkında deep seviyede hukukî mütalaa hazırla; bütünleştirici değerlendirme, sonuç ve kaynakça/alıntılar ekle.”

`socratlegal_yardim` aracı veya `legalai://capabilities` kaynağı, istemcinin desteklediği araçları ve örnek istemleri gösterir. Bilirkişi raporu akışı üretim modülüdür; teknik alan kullanıcı tarafından verilmezse sistem rapordan alanı çıkarmaya çalışır, belirsiz sonuçları varsayım olarak etiketler ve teknik karşı argümanları hukuk kaynaklarıyla bağlamaya çalışır.

Sözleşme incelemesi için `socratlegal_sozlesme_incele` aracını veya doğal dilde “Bu sözleşmeyi madde madde, kaynaklı ve karşı görüşleriyle incele” istemini kullanın.

Hukukî mütalaa için `socratlegal_hukuki_mutalaa` aracını veya doğal dilde mütalaa talebini kullanabilirsiniz. `brief`, `standard`, `deep` ve `exhaustive` ayrıntı seviyeleri vardır; mütalaa çıktısı önce özet, sonra ayrıntılı değerlendirme, sonuç ve kaynakça düzeninde hazırlanır. Ham düşünce zinciri gösterilmez; bunun yerine gerekçeler, varsayımlar, belirsizlikler ve kaynak bağlantıları gösterilir.

Kalite profili istemci tarafından seçilebilir: `auto` (model adına göre uyarlanır), `balanced`, `frontier` veya `exhaustive`. Bu profiller çıktı sözleşmesini, araştırma genişliğini ve eleştiri turunu düzenler; daha küçük/ hızlı bir modelin teknik sınırlarını ortadan kaldırdığı garanti edilmez. Doğrudan uygulanabilir kaynak bulunmadığında SocratLegal, aday kaynakları “doğrudan otorite” diye sunmaz; analoji benzerliklerini, farklarını ve kanunilik/ölçülülük sınırlarını ayrı gösterir.

Taranmış PDF veya görüntü bilirkişi raporlarında yerel OCR eklentisi kurulmuşsa PDF sayfaları da yerelde metne çevrilir. OCR motoru yoksa araç `ocr_required` uyarısı verir; okunmamış sayfalardan teknik veya hukuki sonuç üretmez. Kaynak kod kurulumunda `uv sync --extra ocr` ile Python bileşenleri kurulmalı, Windows'ta ayrıca Tesseract ve `tur` dil verisi bulunmalıdır.

Tüm sonuçlar bağlayıcı hukuki görüş değil, kaynaklı ve ihtimalli analizdir. Kişisel veriler dış çağrıdan önce maskelenir; IDE'nin kendi veri politikası ayrıca incelenmelidir.
