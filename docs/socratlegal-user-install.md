# SocratLegal kullanıcı kurulumu

SocratLegal ayrı bir web sitesi, hosting veya sürekli açık bir sunucu gerektirmez. Kullanıcının bilgisayarında çalışan yerel STDIO MCP sunucusudur.

## Kurulum durumu

Portable kurulum bu sürümde kullanıcıya sunulmuyor; ZIP akışı da son kullanıcı için desteklenmiyor. Bu rehber, desteklenen kaynak kod kurulumunu anlatır.

## Gerekenler

Python 3.11 veya üstü, `uv`, Git ve projeyi indirebileceğiniz bir klasör gerekir. Bağımlılıkların ilk indirilmesi için internet bağlantısı da gereklidir.

- Python: https://www.python.org/downloads/
- uv: https://docs.astral.sh/uv/getting-started/installation/

## Kurulum

Projeyi GitHub'dan indirin ve proje klasörüne geçin:

```powershell
git clone https://github.com/hknrslnby-eng/legalai-yargi-mcp.git
cd legalai-yargi-mcp
uv sync --frozen --dev
```

## API anahtarları

Repo kökündeki `.env` dosyasını oluşturmak için örnek dosyayı kopyalayın:

```powershell
Copy-Item .\legalai.env.example .\.env
notepad .\.env
```

İlgili sağlayıcının satırındaki `=` işaretinden sonra kendi API anahtarınızı yazın. Tırnak işareti veya başta/sonda boşluk kullanmayın. Anahtarı GitHub'a, ekran görüntüsüne veya destek mesajına koymayın. `LEGALAI_LLM_PROVIDER=auto` seçeneği, bulunan ve görev için desteklenen sağlayıcıyı seçer. API anahtarı vermeden de IDE'nin kendi aboneliğiyle yerel MCP araçları kullanılabilir.

`legalai.env.example` içindeki sağlayıcı satırları boş örnektir; hepsinin aynı anda etkin olduğu anlamına gelmez.

## IDE'ye bağlama

Repo kökünde aşağıdaki komut seçtiğiniz istemciye yerel MCP kaydını ekler:

```powershell
uv run socratlegal install --install-dir . --ide cursor
```

Desteklenen istemciler Cursor, Codex, Claude Desktop, Antigravity ve VS Code'dur. `--ide all --only-installed` bilgisayarda zaten bulunan destekli istemcilere kayıt ekler; hepsini zorunlu olarak kurmaz. IDE ayarında URL girilmez: komut, argümanlar ve çalışma klasörü yerel olarak yazılır. Mevcut MCP kayıtları korunur.

## Belge yüklendiğinde hangi yetenek kullanılır?

Tebligat, ihtar, dava dilekçesi, savunma talebi veya iddianame gibi süreci tetikleyen bir belge için sohbete “önce eksik bilgi-belge-delil listesini çıkar, sonra dava dışı ve dava içi çözüm yollarını süre ve merci riskleriyle karşılaştır” yazın. SocratLegal bunu `socratlegal_onbilgi_ve_strateji` yeteneğine yönlendirir. Tüm sonuçlar koşullu, analysis-only ve non-binding araştırma taslağıdır.

## Dilekçe üslup profili

Kullanıcı isterse kendi örnek dilekçelerinden yalnızca başlık, atıf biçimi, ton ve argüman sırası gibi yapısal sinyaller çıkarılabilir. Ham örnekler, kişisel veriler veya örnek metinler GPT/Claude/Codex genel eğitimine gönderilmez; profil yerel türetilmiş metadata'dır. Profilin bir işlemde uygulanması için `style_profile_consent=true` açık kullanıcı onayı gerekir. Profil temizlendiğinde türetilmiş yerel metadata da kaldırılmalıdır; hukuki kaynak ve güvenlik başlıkları üslup profili tarafından değiştirilemez.

GitHub repo adresi bir MCP `url` endpoint'i değildir. Hosting kurulmadığı için IDE ayarında `url` yerine yerel `command`, `args` ve `cwd` kaydı kullanılır.

## Güncellemeler

Yeni fork commitlerini almak için proje klasöründe:

```powershell
git fetch origin
git pull --ff-only
uv sync --frozen
```

Bu işlem yerel kodu ve Python bağımlılıklarını günceller; `.env` dosyanız korunur. Upstream'deki değişiklikler bu fork'a otomatik gelmez. Yeni adapter, kurum/kurul bağlantısı veya backend değişikliği önce fork maintainer'ı tarafından incelenip merge edilmeli ve test edilmelidir. Yeni bir corpus kaynağı bağlanırsa gerektiğinde ayrıca `uv run socratlegal corpus sync ...` çalıştırılır.

IDE'deki MCP kaydı aynı kalır; yeni bir cihaz veya yeni bir IDE için IDE'ye bağlama komutunu tekrar çalıştırmanız yeterlidir.

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

## Tüm kurulu IDE'lere kaynak koddan kayıt

Repo kökünde aşağıdaki komutu çalıştırın:

```powershell
uv run socratlegal install --install-dir . --ide all --only-installed
```

Komut yalnızca bilgisayarda bulunan destekli istemcilere kayıt ekler; bulunmayan istemcileri atlar. Mevcut sunucu kayıtları korunur.
