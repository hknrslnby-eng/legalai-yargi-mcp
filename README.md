# SocratLegal

SocratLegal, hukuk araştırması ve hukuki metin hazırlığı için yerel çalışan bir MCP yazılımıdır. Bir IDE'nin sohbet ekranından doğal Türkçe veya desteklenen diğer dillerde soru sorabilirsiniz. Çıktılar araştırma ve taslak niteliğindedir; bağlayıcı hukuki görüş değildir.

## En kolay kurulum: Windows x64 portable paket

1. GitHub Releases sayfasından `windows-x64` ZIP paketini indirin (https://github.com/hknrslnby-eng/legalai-yargi-mcp/releases/tag/v0.2.5)
2. ZIP'i yazma izniniz olan bir klasöre açın.
3. Terminal kullanmak istemiyorsanız ana klasördeki `install.ps1` dosyasına sağ tıklayıp **PowerShell ile çalıştır** seçeneğini kullanın.
4. Kurulacak istemciyi seçin. Örneğin `.install.ps1 -Ide cursor` yalnızca Cursor'a ekleme yapar. `-Ide all -OnlyInstalled` bilgisayarda zaten bulunan destekli istemcileri seçer.
5. IDE'yi yeniden başlatın ve sohbete `SocratLegal yardım` yazın.

Bu sürümde hazır portable paket yalnızca 64 bit Windows içindir. macOS/Linux için portable paket sözü verilmez. Bu sistemlerde kaynak kod kurulumu kullanılabilir.

Yeni portable sürümleri tarayıcıdan elle aramak yerine, portable klasöründeki `update.cmd` dosyasına çift tıklayarak kullanıcı onaylı, HTTPS ve SHA-256 kontrollü güncelleme yapabilirsiniz. `config`, `data`, API anahtarları ve yerel corpus korunur.

## Kaynak kodla kurulum

Python 3.11 veya üstü ve `uv` gerekir:

Python resmi indirme sayfası: https://www.python.org/downloads/
`uv` resmi kurulum rehberi: https://docs.astral.sh/uv/getting-started/installation/

`uv` için Windows PowerShell kurulumu:
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

Python ve `uv` kurulumu mevcut veya tamamlanmışsa, kaynak kodu yerel cihazınıza terminalden kurabilirsiniz:

```powershell
uv sync --frozen --dev
uv run socratlegal install --install-dir . --ide cursor
uv run socratlegal-mcp
```

Desteklenen IDE/istemciler: Codex, Cursor, Claude Desktop, Antigravity ve VS Code. Hepsi otomatik olarak seçilmez; kurulumu yapan kişi istediği istemciyi seçer. `--ide all` adayların hepsini gösterir, `--only-installed` yalnızca bilgisayarda bulunanları ekler.

IDE ayarında URL girilmez. Yerel sunucunun komutu, argümanları ve klasörü kullanılır. CLI, hızlı kontrol ve otomasyon içindir; günlük kullanım IDE sohbetinden yapılabilir.

## API anahtarı

API anahtarı kullanmak zorunlu değildir. IDE'nin kendi Claude, GPT veya Gemini aboneliği varsa host model bu abonelikle çalışabilir.

Portable yöntemde kurulumdan sonra `config\.env` dosyasını açın. Örneğin OpenAI kullanacaksanız `OPENAI_API_KEY=` satırının sağına kendi anahtarınızı yazın. Kaynak kod yönteminde aynı iş için repo kökündeki `.env` dosyası kullanılır. Anahtarı tırnak içine almayın, başına/sonuna boşluk koymayın ve bu dosyayı GitHub'a göndermeyin.

`legalai.env.example` boş bir örnektir. Anthropic, OpenAI, OpenRouter, DeepSeek, Kimi, GLM, Gemini, Grok/xAI, Composer, Hugging Face, GitHub Copilot ve başka önde gelen sağlayıcılar için alanlar bulunur. Bir alanın bulunması o sağlayıcının kurulu sürümde etkin olduğu anlamına gelmez; yalnızca gerçekten desteklenen ve seçilen sağlayıcı çalışır.

Portable paket kullanmayan ve repoyu kaynak kod olarak kuran kullanıcılar API anahtarlarını repo kökündeki `.env` dosyasına yazar.

Önce örnek dosyayı kopyalayın:

```powershell
Copy-Item .\legalai.env.example .\.env
notepad .env
```

Örnek:

```dotenv
LEGALAI_LLM_PROVIDER=gemini
GEMINI_API_KEY=buraya_kendi_api_anahtariniz
```

Otomatik sağlayıcı seçimi için:

```dotenv
LEGALAI_LLM_PROVIDER=auto
GEMINI_API_KEY=
GROQ_API_KEY=
OPENROUTER_API_KEY=
DEEPSEEK_API_KEY=
```

`auto` seçeneğinde sistem, anahtarı bulunan ve görev için desteklenen sağlayıcıyı seçer.

## Yetenekler

Kullanıcı araç adlarını ezberlemek zorunda değildir. İsteğini normal cümleyle yazabilir veya `socratlegal_yardim` aracını kullanabilir.

| Yetenek | Ne yapar? | Alt yetenekler |
|---|---|---|
| Kaynak arama ve çapraz sorgu | Soruyu yerel corpus, canlı resmi adapter'lar ve uygun uluslararası kaynaklarda arar. | Kurum/mahkeme seçimi, keyword dışı bağlam algısı, kaynak durumu, provenance, atıf ve hata ayrımı |
| Katmanlı analiz | Hukuki normları, içtihatları ve maddi olayı birlikte inceler. | Tarih ve yürürlük, görev-yetki, süre, karşı görüş, belirsizlik, teknik lens, davranış/iş akışı lensi |
| Ön bilgi | Müvekkile gelen tebligat, ihtar, dava dilekçesi, iddianame veya mahkeme kararı gibi belgeyi; yapılabilecek hukuki yolları, süre ve merci risklerini, ilgili hukuk alanlarını, eksik bilgi-belgeleri, gerekli delilleri ve alternatif stratejileri çıkararak katmanlı biçimde inceler. | Belge türü ve usul aşaması, hukuki yollar, süre ve merci, karşı argümanlar, eksik bilgi-belge-deliller, kullanıcıya sorulacak sorular |
| Strateji | Dava içi ve dava dışı seçenekleri karşılaştırır. | Dava, icra, arabuluculuk, idari başvuru, sulh, 35/A, ceza yolu sinyali, geri dönüş/risk karşılaştırması |
| Hukuki mütalaa | 13 bölümlü, kaynaklı ve ihtimalli mütalaa taslağı üretir. | Yönetici özeti, hukuki çerçeve, olay uygulaması, karşı argüman, birleştirici değerlendirme, sonuç, kaynakça |
| Dilekçe işlemleri | Dilekçe hazırlar, inceler, kısaltır veya uzatır. | Usul başlıklarını koruma, kaynak/alıntı politikası, teknik ve operasyonel olgular, çok dilli çıktı |
| Agresif karşı taraf | Kullanıcının pozisyonunu karşı taraf gözüyle sınar. | Karşı argüman, karşıt içtihat, zayıf nokta, forum/süre, alternatif çözüm yolları |
| Derin araştırma | Karmaşık soruyu alt sorulara bölerek araştırır. | Kaynak doğrulama, çelişki, host model sentez talimatı |
| Bilirkişi akışı | Bilirkişi raporunu teknik ve hukuki yönden sınar veya itiraz dilekçesi taslağı üretir. | Teknik bulgu matrisi, alternatif teknik açıklama, eksik veri, ek rapor/yeni bilirkişi talebi, hukuk bağlantısı |
| Sözleşme inceleme | Sözleşmeyi madde ve operasyon bakımından inceler. | Hukuki nitelik, risk, eksik hüküm, yabancı unsur, işleyiş etkisi |
| Atıf ve gizlilik | Kaynak alıntılarını kontrol eder, dış çağrı öncesi PII'yi maskeler. | Belge kimliği, provenance, yerel geri açma, gizlilik uyarısı |
| Corpus yönetimi | Yerel belge ekler, durum gösterir ve izinli kaynakları corpus'a alır. | Corpus-only/live ayrımı, sürüm, checksum, revizyon geçmişi |

## Özel uzmanlık lensleri

- Rekabet: Hukuk yanında iktisat ve işletme bakışı kullanılır. Ürün/coğrafi pazar, pazar payı ve yıllara göre değişim, satış hacmi/ciro, rakipler, tedarikçiler, müşteriler, değer zinciri, giriş engelleri, fiyat/maliyet, sektör seyri ve resmi veya itibarlı sektör raporları istenir.
- Ticaret savunması: Anti-damping, sübvansiyon ve korunma tedbirlerinde mevzuat, soruşturma akışı, zarar/nedensellik, hesaplama ve delil stratejisi birlikte ele alınır.
- KVKK: KVKK ana çerçevesine, olayla ilgiliyse NIS-1, NIS-2, siber güvenlik, bilişim, veri yönetimi ve gerektiğinde idare/ceza veya başka hukuk alanları eklenir. İlgisiz alanlar otomatik olarak eklenmez.
- Teknik ve maddi olay lensi: Kullanıcının sağladığı girdiye göre maddi olay ve teknik ayrıntılara ilişkin iş-süreç akışı, operasyonlar, teamüller ve benzeri süreçler ilgili alanın kıdemli uzmanı gözüyle incelenir; bu katman hukuki değerlendirmeyi destekler, onun yerine geçmez.

## Çok dilli hukuk çıktısı

Türkçe yanında İngilizce, Fransızca, Almanca, Rusça, Arapça, İspanyolca ve Çince çıktı istenebilir. Hukuki terminoloji, kurum/mahkeme adları, karar-mevzuat kimlikleri ve kaynak provenance'ı korunur. Sistem sertifikalı veya yeminli tercüme yaptığını iddia etmez. Dilekçe kısaltmada içtihat alıntıları varsayılan olarak korunur; kaldırılması için açık onay gerekir.

## Corpus, canlı kaynak ve sınırlar

Corpus kurulmadan da yapılandırılmış canlı adapter'ların erişebildiği kaynaklarda arama yapılabilir. Kaynağın yanında `live_ready`, `corpus_only`, `verification_pending` veya `disabled` durumu gösterilir. Yeni resmi belgeler canlı adapter ile alınabilir veya kullanıcı tarafından maskelenmiş/kamuya açık biçimde corpus'a eklenebilir. Canlı erişim yoksa sistem bunu sonuçta saklamaz; corpus'ta olmayan güncel karar kesinlikle varmış gibi sunulmaz.

SocratLegal upstream servisin kapanmasına dayanmaz; yerel kod, yerel corpus ve yapılandırılmış adapter'lar fork içinde bulunur. Upstream'de yeni bir değişiklik otomatik olarak fork'a veya kullanıcının portable paketine gelmez. Yeni fork release'i açıkça indirilir; `data`, `config` ve IDE kayıtları korunur.

Due diligence bu sürümde aktif bir üretim yeteneği olarak sunulmaz.

## Slash sözlüğü

Slash ifadeleri kullanıcının hangi yetenek veya uzmanlık bakışını istediğini kısa yoldan belirtir. Bir IDE'nin slash menüsü göstermesi host uygulamasına bağlıdır. Menü görünmese de aynı ifadeyi doğal cümle içinde yazabilirsiniz.

| Slash ifadesi | Gerçek yetenek veya bağlantılı araç | Ne yapar? | Durum |
|---|---|---|---|
| `/yardim` | `socratlegal_yardim` | Tüm yetenekleri, kullanım alanlarını ve örnek talepleri gösterir. | Aktif MCP aracı |
| `/kaynak_ara` | `socratlegal_kaynak_ara` | Yerel corpus, canlı resmi adapter'lar, mahkemeler ve uluslararası kaynaklarda arama yapar. | Aktif MCP aracı |
| `/katmanli_analiz` | `socratlegal_katmanli_analiz` | Hukuki normları, içtihatları, olayları, tarihleri, süreleri, görev-yetkiyi ve belirsizlikleri birlikte inceler. | Aktif MCP aracı |
| `/onbilgi` | `socratlegal_onbilgi_ve_strateji` | Müvekkile gelen belge üzerinden yapılabilecek hukuki yolları, riskleri, eksik bilgi-belgeleri ve gerekli delilleri çıkarır. | Aktif MCP aracı |
| `/strateji` | Ön bilgi ve strateji akışı | Dava, itiraz, icra, arabuluculuk, idari başvuru, sulh ve gerektiğinde ceza yollarını karşılaştırır. | Aktif akış |
| `/mutalaa` | `socratlegal_hukuki_mutalaa` | 13 bölümlü, kaynaklı ve ihtimalli hukuki mütalaa taslağı üretir. | Aktif MCP aracı |
| `/dilekce` | `socratlegal_dilekce_*` | Dilekçe hazırlar, inceler, kısaltır veya uzatır. | Aktif MCP araç grubu |
| `/bilirkişi` | `socratlegal_bilirkisi_raporu_*` | Bilirkişi raporunu teknik ve hukuki açıdan inceler veya itiraz dilekçesi hazırlar. | Aktif MCP araç grubu |
| `/karsi_taraf` | `socratlegal_agresif_karsi_taraf` | Karşı tarafın güçlü argümanlarını, karşıt içtihatları ve alternatif çözüm yollarını çıkarır. | Aktif MCP aracı |
| `/derin_arastirma` | `socratlegal_derin_arastirma` | Karmaşık soruyu alt sorulara bölerek çok kaynaklı araştırma yapar. | Aktif MCP aracı |
| `/sozlesme` | `socratlegal_sozlesme_incele` | Sözleşmeyi madde, risk, eksiklik ve operasyonel etkileriyle inceler. | Aktif MCP aracı |
| `/alinti_dogrula` | `alinti_dogrula` | Taslakta kullanılan kaynak ve belge atıflarını kontrol eder. | Aktif yetenek |
| `/pii_maskele` | `pii_maskele` | Dış çağrıdan önce kişisel verilerin yerelde maskelenmesini sağlar. | Aktif yetenek |
| `/corpus` | Corpus durum, belge ekleme ve sync araçları | Yerel corpus durumunu gösterir, belge ekler ve izinli kaynakları corpus'a alır. | Aktif MCP araç grubu |
| `/guncelleme` | `socratlegal_guncelleme_kontrol` | Yeni portable sürüm metadata’sını kontrol eder; otomatik kurulum yapmaz. | Aktif MCP aracı |
| `/teknik_lens` | Teknik ve operasyonel katman | Maden, siber olay, üretim, dağıtım, IBAN/kripto ve benzeri maddi süreçleri ilgili teknik uzman bakışıyla inceler. | Aktif yönlendirme lensi |
| `/capraz_sorgu` | Kaynak yönlendirme ve `socratlegal_kaynak_ara` | Keyword beklemeden, bağlamla ilgili kurum, mahkeme, corpus ve uluslararası kaynakları birlikte değerlendirir. | Aktif yönlendirme lensi |
| `/rekabet` | Rekabet persona ve competition intake | Hukukun yanında iktisat, işletme, pazar payı, rakipler, tedarikçiler, müşteriler, zincir, giriş engelleri ve sektör raporlarını inceler. | Aktif yönlendirme lensi |
| `/anti_damping` | Ticaret savunması persona ve kaynak yönlendirme | Anti-damping, sübvansiyon ve korunma tedbirlerinde soruşturma, damping marjı, zarar, nedensellik ve delil stratejisini inceler. | Aktif yönlendirme lensi |
| `/kvkk_nis` | KVKK related-law selection | KVKK’ya olayla ilgili olduğu ölçüde NIS-1, NIS-2, siber güvenlik, idare ve ceza perspektiflerini ekler. | Aktif yönlendirme lensi |

`/teknik_lens`, `/capraz_sorgu`, `/rekabet`, `/anti_damping` ve `/kvkk_nis` bağımsız MCP araçları değildir. Bunlar mevcut analiz, mütalaa, strateji, dilekçe ve kaynak arama akışlarına teknik, çapraz kaynak, rekabet, ticaret savunması veya KVKK-NIS-siber güvenlik perspektifi ekleyen aktif yönlendirme lensleridir. Host uygulaması slash menüsünü destekliyorsa menüden, desteklemiyorsa doğal dille kullanılabilir.

## Sistem gereksinimleri ve güvenlik

Portable Windows x64 için yazma izni olan bir klasör ve internet bağlantısı (bağımlılıkların ilk indirilmesi için) yeterlidir. Kaynak kod yönteminde Python 3.11+ ve `uv` gerekir. API anahtarları kullanıcıya aittir; ücret, kota ve sağlayıcı veri politikası sağlayıcıya göre değişir. Tüm sonuçlar `analysis_only` ve `non_binding` niteliğindedir.

Lisans ve fork atıfları için [LICENSE](LICENSE) ve [NOTICE.md](NOTICE.md) dosyalarına bakın. Kurulum ayrıntıları için [portable rehberini](docs/socratlegal-user-install.md), IDE ayarları için [MCP istemci rehberini](docs/mcp-client-setup.md) okuyun.
