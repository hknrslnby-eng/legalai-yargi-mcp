# SocratLegal

SocratLegal, hukuk araştırması ve hukuki metin hazırlığı için yerel çalışan bir MCP yazılımıdır. Bir IDE'nin sohbet ekranından doğal Türkçe veya desteklenen diğer dillerde soru sorabilirsiniz. Çıktılar araştırma ve taslak niteliğindedir; bağlayıcı hukuki görüş değildir.

## En kolay kurulum: Windows x64 portable paket

1. GitHub Releases sayfasından `windows-x64` ZIP paketini indirin.
2. ZIP'i yazma izniniz olan bir klasöre açın.
3. `install.ps1` dosyasını çalıştırın.
4. Kurulacak istemciyi seçin. Örneğin `.install.ps1 -Ide cursor` yalnızca Cursor'a ekleme yapar. `-Ide all -OnlyInstalled` bilgisayarda zaten bulunan destekli istemcileri seçer.
5. IDE'yi yeniden başlatın ve sohbete `SocratLegal yardım` yazın.

Bu sürümde hazır portable paket yalnızca 64 bit Windows içindir. macOS/Linux için portable paket sözü verilmez. Bu sistemlerde kaynak kod kurulumu kullanılabilir.

## Kaynak kodla kurulum

Python 3.11 veya üstü ve `uv` gerekir:

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

## Yetenekler

Kullanıcı araç adlarını ezberlemek zorunda değildir. İsteğini normal cümleyle yazabilir veya `socratlegal_yardim` aracını kullanabilir.

| Yetenek | Ne yapar? | Alt yetenekler |
|---|---|---|
| Kaynak arama ve çapraz sorgu | Soruyu yerel corpus, canlı resmi adapter'lar ve uygun uluslararası kaynaklarda arar. | Kurum/mahkeme seçimi, keyword dışı bağlam algısı, kaynak durumu, provenance, atıf ve hata ayrımı |
| Katmanlı analiz | Hukuki normları, içtihatları ve maddi olayı birlikte inceler. | Tarih ve yürürlük, görev-yetki, süre, karşı görüş, belirsizlik, teknik lens, davranış/iş akışı lensi |
| Ön bilgi | Tebligat, ihtar, dava dilekçesi veya iddianame gibi belgeyi ilk kez düzenler. | Eksik bilgi-belge-delil listesi, öncelik, süre/merci riski, kullanıcıya soru sorma |
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
- Teknik ve maddi olay lensi: Maden ruhsatı, siber olay, IBAN/kripto akışı, üretim-dağıtım zinciri ve benzeri süreçler ilgili alanın kıdemli uzmanı gözüyle incelenir; bu katman hukuki değerlendirmeyi destekler, onun yerine geçmez.

## Çok dilli hukuk çıktısı

Türkçe yanında İngilizce, Fransızca, Almanca, Rusça, Arapça, İspanyolca ve Çince çıktı istenebilir. Hukuki terminoloji, kurum/mahkeme adları, karar-mevzuat kimlikleri ve kaynak provenance'ı korunur. Sistem sertifikalı veya yeminli tercüme yaptığını iddia etmez. Dilekçe kısaltmada içtihat alıntıları varsayılan olarak korunur; kaldırılması için açık onay gerekir.

## Corpus, canlı kaynak ve sınırlar

Corpus kurulmadan da yapılandırılmış canlı adapter'ların erişebildiği kaynaklarda arama yapılabilir. Kaynağın yanında `live_ready`, `corpus_only`, `verification_pending` veya `disabled` durumu gösterilir. Yeni resmi belgeler canlı adapter ile alınabilir veya kullanıcı tarafından maskelenmiş/kamuya açık biçimde corpus'a eklenebilir. Canlı erişim yoksa sistem bunu sonuçta saklamaz; corpus'ta olmayan güncel karar kesinlikle varmış gibi sunulmaz.

SocratLegal upstream servisin kapanmasına dayanmaz; yerel kod, yerel corpus ve yapılandırılmış adapter'lar fork içinde bulunur. Upstream'de yeni bir değişiklik otomatik olarak fork'a veya kullanıcının portable paketine gelmez. Yeni fork release'i açıkça indirilir; `data`, `config` ve IDE kayıtları korunur.

Due diligence bu sürümde aktif bir üretim yeteneği olarak sunulmaz.

## Slash sözlüğü

Bazı IDE'ler `/` menüsü gösterebilir; görünüm IDE'ye bağlıdır. Aynı ifadeleri doğal dille de yazabilirsiniz:

`/yardim` · `/kaynak_ara` · `/katmanli_analiz` · `/onbilgi` · `/strateji` · `/mutalaa` · `/dilekce` · `/bilirkişi` · `/teknik_lens` · `/capraz_sorgu` · `/rekabet` · `/anti_damping` · `/kvkk_nis`

## Sistem gereksinimleri ve güvenlik

Portable Windows x64 için yazma izni olan bir klasör ve internet bağlantısı (bağımlılıkların ilk indirilmesi için) yeterlidir. Kaynak kod yönteminde Python 3.11+ ve `uv` gerekir. API anahtarları kullanıcıya aittir; ücret, kota ve sağlayıcı veri politikası sağlayıcıya göre değişir. Tüm sonuçlar `analysis_only` ve `non_binding` niteliğindedir.

Lisans ve fork atıfları için [LICENSE](LICENSE) ve [NOTICE.md](NOTICE.md) dosyalarına bakın. Kurulum ayrıntıları için [portable rehberini](docs/socratlegal-user-install.md), IDE ayarları için [MCP istemci rehberini](docs/mcp-client-setup.md) okuyun.
