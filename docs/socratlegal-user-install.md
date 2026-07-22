# SocratLegal kullanıcı kurulumu

SocratLegal ayrı bir web sitesi, hosting veya sürekli açık bir sunucu gerektirmez. Kullanıcının bilgisayarında çalışan yerel STDIO MCP sunucusudur.

## Önerilen yol: portable paket

1. GitHub deposunun **Releases** sayfasından `windows-x64` ZIP paketini indirin. Bu sürümde resmî portable paket yalnızca 64 bit Windows içindir; macOS/Linux portable paketi vaat edilmez.
2. Paketi yazma izniniz olan bir klasöre çıkartın; örneğin `C:\Users\Siz\SocratLegal`.
3. Windows'ta `install.ps1` dosyasını çalıştırın.
4. IDE'yi yeniden başlatın veya MCP sunucularını yeniden yükleyin.
5. Sohbete `SocratLegal sağlık kontrolü yap` yazın.

Portable pakette Windows x64 için gerekli `uv.exe` çalıştırıcısı bulunur. Bu nedenle sistemde ayrıca Python, uv veya GitHub CLI kurulması beklenmez. İlk çalıştırmada uv, `uv.lock` bağımlılıklarını kendi önbelleğine indirebilir; bu hosting kurulması değildir.

Kurulum betiği desteklenen istemcileri gösterir; hepsini zorunlu olarak kurmaz. `-Ide cursor` gibi bir seçim yalnızca seçilen istemciye kayıt ekler. `-Ide all -OnlyInstalled` ise bilgisayarda zaten bulunan destekli istemcileri seçer.

Windows örneği:

```powershell
.\install.ps1 -Ide cursor
```

## API anahtarı nereye yazılır?

Kurulumdan sonra portable klasöründe `config\.env` dosyası oluşturulur. Bu dosyayı Not Defteri ile açıp kullanmak istediğiniz sağlayıcının karşısındaki boş yere anahtarı yapıştırın; örneğin `OPENAI_API_KEY=` satırının sağına anahtarı yazın. Tırnak işareti eklemeyin, anahtarı başına veya sonuna boşluk koymadan tek satırda tutun ve dosyayı kaydedin. Anahtarları GitHub'a, ekran görüntüsüne veya destek mesajına koymayın. Anahtar vermeden de host IDE'nin kendi aboneliğiyle yerel MCP araçlarını kullanabilirsiniz.

`legalai.env.example` içindeki sağlayıcı satırları boş örnektir. Dosyada çok sayıda sağlayıcı adı bulunması, hepsinin aynı anda etkin olduğu anlamına gelmez; kurulu sürüm yalnızca desteklediği ve seçilen sağlayıcıyı kullanır. Kullanıcıya ait anahtarlar portable güncellemede `config` klasöründe korunur.

Birden fazla istemci için:

```powershell
.\install.ps1 -Ide cursor -Ide codex -Ide antigravity
```

Kurulumdan önce ne yapılacağını görmek için `-DryRun`, ekrandaki iki bitişik JSON nesnesinden oluşan eski ayarı onarmayı denemek için `-Repair` kullanılır.

## Manuel checkout yolu

Bu yol geliştirici veya kaynak kodla çalışmak isteyen kullanıcı içindir. Bilgisayarda Python 3.11 veya üstü ve `uv` bulunmalıdır. Repo klasöründe `uv sync --frozen --dev` çalıştırılır; ardından `uv run socratlegal install --install-dir . --ide cursor` komutu seçilen IDE'ye yerel MCP kaydını ekler. Cursor, Codex, Claude Desktop, Antigravity ve VS Code için ayrı kayıt seçilebilir; `--ide all` hepsini aday olarak tarar, `--only-installed` yalnızca mevcut olanları kaydeder. IDE'de URL girilmez: komut, argümanlar ve çalışma klasörü yerel olarak yazılır.

Bu yöntemde API anahtarı repo kökündeki `.env` dosyasına yazılır. Portable yöntemde ise `config\.env` kullanılır. İki yöntemde de `.env` dosyası repoya gönderilmemelidir.

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

Upstream depoda veya bu fork'ta yeni adapter, kurum/kurul bağlantısı ya da backend kodu eklenirse bu değişiklik portable kullanıcılara kendiliğinden gelmez; kullanıcı yeni fork release'ini indirip checksum kontrolünden sonra uygulamalıdır. Yeni bir corpus veritabanı dosyası release paketine otomatik olarak eklenmez ve mevcut kullanıcı verisinin üzerine yazılmaz. Yeni sürümde yeni canlı adapter veya corpus kaynağı kodu varsa, kullanıcı güncellemeden sonra ilgili corpus sync işlemini açıkça çalıştırarak yeni kaynakları yerel corpus'a alır.

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
## Tüm kurulu IDE'lere tek portable kayıt

Portable klasöründeki kurulum betiği mevcut desteklenen istemcileri tespit eder. Windows'ta `scripts\\install.ps1 -Ide all -OnlyInstalled`, macOS/Linux'ta `scripts/install.sh --only-installed` komutları yalnızca mevcut Cursor, Antigravity, VS Code, Claude ve Codex kayıtlarına ekleme yapar; bulunmayan istemciler `skipped` olarak raporlanır. Sonradan yeni bir IDE kurarsanız aynı betiği tekrar çalıştırmanız yeterlidir; portable paketi yeniden indirmeniz gerekmez. Mevcut sunucular korunur ve değişiklikten önce yedek alınır.
