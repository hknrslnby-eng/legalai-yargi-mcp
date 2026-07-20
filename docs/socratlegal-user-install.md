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

Geliştirici veya kaynak koddan çalışan kullanıcı repoyu indirip sistemine `uv` kurduktan sonra şunları çalıştırabilir:

```powershell
uv sync --frozen --dev
uv run socratlegal install --install-dir "C:\SocratLegal" --ide cursor
```

Bu yol Python ve uv gerektirir; normal kullanıcı için portable paket tercih edilir. GitHub repo adresi bir MCP `url` endpoint'i değildir. Hosting kurulmadığı için IDE ayarında `url` yerine yerel `command`, `args` ve `cwd` kaydı kullanılır.

## Güncellemeler

Yeni özellikler yayınlandığında aynı portable paketin yeni sürümü indirilir. Uygulama güncellemesi `data` klasörünü, yerel corpus'u, belgeleri ve API anahtarlarını paketten silmez. Yeni sürüm önce geçici alanda açılır, SHA-256 doğrulanır, sonra `app.previous` yedeği bırakılarak devreye alınır. Başlangıç kontrolü başarısız olursa önceki sürüme dönülür.

Güncelleme kontrolü yalnızca sürüm metadata'sını okur ve varsayılan olarak 24 saatte bir yapılır; kullanıcı belgelerinin metni gönderilmez.

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

`socratlegal_yardim` aracı veya `legalai://capabilities` kaynağı, istemcinin desteklediği araçları ve örnek istemleri gösterir. Bilirkişi raporu akışı üretim modülüdür; teknik alan kullanıcı tarafından verilmezse sistem rapordan alanı çıkarmaya çalışır, belirsiz sonuçları varsayım olarak etiketler ve teknik karşı argümanları hukuk kaynaklarıyla bağlamaya çalışır.

Tüm sonuçlar bağlayıcı hukuki görüş değil, kaynaklı ve ihtimalli analizdir. Kişisel veriler dış çağrıdan önce maskelenir; IDE'nin kendi veri politikası ayrıca incelenmelidir.
