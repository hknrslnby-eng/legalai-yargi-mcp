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

Portable yöntemde kurulumdan sonra `config\.env` dosyasını açın. Sunucu tarafı sentez için kullandığınız etkin sağlayıcının anahtarını ilgili satıra yazın: `GEMINI_API_KEY=...`, `OPENROUTER_API_KEY=...`, `DEEPSEEK_API_KEY=...` veya `GROQ_API_KEY=...`. Kaynak kod yönteminde aynı iş için repo kökündeki `.env` dosyası kullanılır. Anahtarı tırnak içine almayın, başına veya sonuna boşluk koymayın ve bu dosyayı GitHub'a göndermeyin.

`LEGALAI_LLM_PROVIDER=auto` varsayılan yönlendirmedir. İsterseniz `gemini`, `openrouter`, `deepseek` veya `groq` seçebilirsiniz. `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, Kimi, GLM, Grok/xAI, Composer, Hugging Face ve GitHub Copilot alanları örnek dosyada bulunabilir; alanın bulunması bu sürümde sunucu tarafı LLM yönlendiricisinin o sağlayıcıyı etkin olarak kullandığı anlamına gelmez.

## Yetenekler

Kullanıcı araç adlarını ezberlemek zorunda değildir. İsteğini normal cümleyle yazabilir veya `socratlegal_yardim` aracını kullanabilir.

| Yetenek | Ne yapar? | Alt yetenekler |
|---|---|---|
| Kaynak arama ve çapraz sorgu | Soruyu yerel corpus, canlı resmi adapter'lar ve uygun uluslararası kaynaklarda arar. | Kurum ve mahkeme seçimi, bağlam algısı, kaynak durumu, provenance, atıf ve hata ayrımı |
| Katmanlı analiz | Hukuki normları, içtihatları ve maddi olayı birlikte inceler. | Tarih ve yürürlük, görev ve yetki, süre, karşı görüş, belirsizlik, teknik lens, davranış ve iş akışı lensi |
| Ön bilgi | Tebligat, ihtar, dava dilekçesi, iddianame veya mahkeme kararı gibi gelen belgeyi; yapılabilecek hukuki yolları, süre ve merci risklerini, ilgili hukuk alanlarını, eksik bilgi-belgeleri ve gerekli delilleri çıkararak katmanlı biçimde inceler. | Belge türü ve usul aşaması, hukuki yollar, süre ve merci, karşı argümanlar, eksik bilgi-belge-deliller, kullanıcıya sorulacak sorular |
| Strateji | Dava içi ve dava dışı seçenekleri karşılaştırır. | Dava, icra, arabuluculuk, idari başvuru, sulh, 35/A, ceza yolu sinyali, geri dönüş ve risk karşılaştırması |
| Hukuki mütalaa | 13 bölümlü, kaynaklı ve ihtimalli mütalaa taslağı üretir. | Yönetici özeti, hukuki çerçeve, olay uygulaması, karşı argüman, birleştirici değerlendirme, sonuç, kaynakça |
| Dilekçe işlemleri | Dilekçe hazırlar, inceler, kısaltır veya uzatır. | Usul başlıklarını koruma, kaynak ve alıntı politikası, teknik ve operasyonel olgular, çok dilli çıktı |
| Agresif karşı taraf | Kullanıcının pozisyonunu karşı taraf gözüyle sınar. | Karşı argüman, karşıt içtihat, zayıf nokta, forum ve süre, alternatif çözüm yolları |
| Derin araştırma | Karmaşık soruyu alt sorulara bölerek araştırır. | Kaynak doğrulama, çelişki analizi, sentez talimatı ve atıf kontrolü |
| Bilirkişi akışı | Bilirkişi raporunu teknik ve hukuki yönden sınar veya itiraz dilekçesi taslağı üretir. | Teknik bulgu matrisi, alternatif teknik açıklama, eksik veri, ek rapor veya yeni bilirkişi talebi, hukuk bağlantısı |
| Sözleşme inceleme | Sözleşmeyi madde ve operasyon bakımından inceler. | Hukuki nitelik, risk, eksik hüküm, yabancı unsur, işleyiş etkisi |
| Atıf ve gizlilik | Kaynak alıntılarını kontrol eder, dış çağrı öncesi kişisel verileri maskeler. | Belge kimliği, provenance, yerel geri açma, gizlilik uyarısı |
| Corpus yönetimi | Yerel belge ekler, durum gösterir ve izinli kaynakları corpus'a alır. | Corpus-only ve canlı ayrımı, sürüm, checksum, revizyon geçmişi |

## Özel uzmanlık lensleri

- Rekabet: Hukuk yanında iktisat ve işletme bakışı kullanılır. Ürün ve coğrafi pazar, pazar payı ve yıllara göre değişim, satış hacmi ve ciro, rakipler, tedarikçiler, müşteriler, değer zinciri, giriş engelleri, fiyat ve maliyet, sektör seyri ve resmi veya itibarlı sektör raporları bağlama göre istenir.
- Ticaret savunması: Anti-damping, sübvansiyon ve korunma tedbirlerinde mevzuat, soruşturma akışı, zarar ve nedensellik, hesaplama ve delil stratejisi birlikte ele alınır.
- KVKK: KVKK ana çerçevesine, olayla ilgiliyse NIS-1, NIS-2, siber güvenlik, bilişim, veri yönetimi ve gerektiğinde idare, ceza veya başka hukuk alanları eklenir. İlgisiz alanlar otomatik olarak eklenmez.
- Teknik ve maddi olay lensi: Maden ruhsatı, siber olay, IBAN ve kripto akışı, üretim ve dağıtım zinciri gibi süreçler ilgili alanın kıdemli uzmanı gözüyle incelenir; bu katman hukuki değerlendirmeyi destekler, onun yerine geçmez.

## Çok dilli hukuk çıktısı

Türkçe yanında İngilizce, Fransızca, Almanca, Rusça, Arapça, İspanyolca ve Çince çıktı istenebilir. Hukuki terminoloji, kurum ve mahkeme adları, karar ve mevzuat kimlikleri ile kaynak provenance'ı korunur. Sistem sertifikalı veya yeminli tercüme yaptığını iddia etmez. Dilekçe kısaltmada içtihat alıntıları varsayılan olarak korunur; kaldırılması için açık onay gerekir.

## Corpus, canlı kaynak ve sınırlar

Corpus kurulmadan da yapılandırılmış canlı adapter'ların erişebildiği kaynaklarda arama yapılabilir. Kaynağın yanında `live_ready`, `corpus_only`, `verification_pending` veya `disabled` durumu gösterilir. Yeni resmi belgeler canlı adapter ile alınabilir veya kullanıcı tarafından maskelenmiş ve kamuya açık biçimde corpus'a eklenebilir. Canlı erişim yoksa sistem bunu sonuçta saklamaz; corpus'ta olmayan güncel karar kesinlikle varmış gibi sunulmaz.

SocratLegal upstream servisin kapanmasına dayanmaz; yerel kod, yerel corpus ve yapılandırılmış adapter'lar fork içinde bulunur. Upstream'de yeni bir değişiklik otomatik olarak fork'a veya kullanıcının portable paketine gelmez. Yeni fork release'i açıkça indirilir; `data`, `config` ve IDE kayıtları korunur.

Due diligence bu sürümde aktif bir üretim yeteneği olarak sunulmaz.

## Slash sözlüğü

Slash ifadeleri kullanıcının hangi yetenek veya uzmanlık bakışını istediğini kısa yoldan belirtir. Bir IDE'nin slash menüsü göstermesi host uygulamasına bağlıdır. Menü görünmese de aynı ifadeyi doğal cümle içinde yazabilirsiniz.

| Slash ifadesi | Bağlandığı yetenek veya MCP aracı | Kullanıcıya etkisi | Durum |
|---|---|---|---|
| `/yardim` | `socratlegal_yardim` | Yetenek kataloğunu, hangi talepte hangi aracın kullanılacağını ve örnekleri gösterir. | Aktif MCP aracı |
| `/kaynak_ara` | `socratlegal_kaynak_ara` | Corpus, canlı resmi adapter'lar, mahkemeler ve bağlama uygun uluslararası kaynaklarda arama yapar. | Aktif MCP aracı |
| `/katmanli_analiz` | `socratlegal_katmanli_analiz` | Norm, içtihat, maddi olay, usul, zaman, delil ve belirsizlik katmanlarını birlikte inceler. | Aktif MCP aracı |
| `/onbilgi` | `socratlegal_onbilgi_ve_strateji` | Gelen belgeye karşı yapılabilecekleri, süreleri, mercileri, riskleri ve gerekli bilgi-belgeleri çıkarır. | Aktif MCP aracı |
| `/strateji` | Çözüm stratejisi promptu ve ön bilgi akışı | Dava, icra, idari başvuru, arabuluculuk, sulh, ceza ve diğer seçenekleri koşullarıyla karşılaştırır. | Aktif yönlendirme |
| `/mutalaa` | `socratlegal_hukuki_mutalaa` | 13 bölümlü, kaynaklı, ihtimalli ve seçilen dilde hukuki mütalaa taslağı üretir. | Aktif MCP aracı |
| `/dilekce` | `socratlegal_dilekce_hazirla`, `..._incele`, `..._kisalt`, `..._uzat` | Dilekçe hazırlar, inceler, kısaltır veya uzatır; kaynak ve usul başlıklarını korur. | Aktif MCP araç grubu |
| `/bilirkisi` | `socratlegal_bilirkisi_raporu_analiz`, `..._dilekce` | Bilirkişi raporunu teknik ve hukuki yönden inceler veya itiraz dilekçesi taslağı üretir. | Aktif MCP araç grubu |
| `/karsi_taraf` | `socratlegal_agresif_karsi_taraf` | Karşı tarafın güçlü argümanlarını, karşıt içtihatlarını ve zayıf noktaları sınar. | Aktif MCP aracı |
| `/derin_arastirma` | `socratlegal_derin_arastirma` | Karmaşık soruyu alt sorulara böler, kaynakları karşılaştırır ve atıfları kontrol eder. | Aktif MCP aracı |
| `/sozlesme` | `socratlegal_sozlesme_incele` | Sözleşmeyi hukuki nitelik, madde riski, eksik hüküm ve operasyonel işleyiş yönünden inceler. | Aktif MCP aracı |
| `/alinti_dogrula` | `alinti_dogrula` | Taslaktaki belge kimliklerini ve kaynak atıflarını bilinen kaynaklarla karşılaştırır. | Aktif MCP aracı |
| `/pii_maskele` | `pii_maskele` | Dış arama veya sunucu tarafı LLM çağrısı öncesinde kişisel verileri yerelde maskeler. | Aktif MCP aracı |
| `/corpus` | `socratlegal_corpus_durum`, `..._belge_ekle`, `..._sync` | Yerel corpus durumunu gösterir, izinli belge ekler ve uygun adapter sonucunu corpus'a alır. | Aktif MCP araç grubu |
| `/guncelleme` | `socratlegal_guncelleme_kontrol` | Yeni sürüm metadata'sını kontrol eder; kendiliğinden indirme veya kurulum yapmaz. | Aktif MCP aracı |
| `/teknik_lens` | Teknik ve maddi olay katmanı | Maden, siber olay, IBAN ve kripto, üretim ve dağıtım gibi akışları ilgili kıdemli uzman bakışıyla hukuka bağlar. | Aktif yönlendirme lensi |
| `/capraz_sorgu` | Bağlamsal kaynak yönlendirme | Yalnızca keyword beklemeden olayla ilgili kurum, mahkeme, corpus ve uluslararası kaynakları birlikte değerlendirir. | Aktif yönlendirme lensi |
| `/rekabet` | Rekabet persona'sı ve kaynak yönlendirme | Hukuki incelemeye iktisat ve işletme katmanı ekler; pazar, rakip, tedarikçi, müşteri, değer zinciri, giriş engeli ve sektör raporlarını bağlama göre ister. | Aktif yönlendirme lensi |
| `/anti_damping` | Ticaret savunması persona'sı ve kaynak yönlendirme | Anti-damping, sübvansiyon ve korunma tedbirlerinde soruşturma, hesaplama, zarar, nedensellik ve delil stratejisini inceler. | Aktif yönlendirme lensi |
| `/kvkk_nis` | KVKK ve ilgili hukuk seçimi | KVKK'ya olayla ilgili olduğu ölçüde NIS-1, NIS-2, siber güvenlik, idare, ceza ve diğer ilgili hukuk perspektiflerini ekler. | Aktif yönlendirme lensi |

`/teknik_lens`, `/capraz_sorgu`, `/rekabet`, `/anti_damping` ve `/kvkk_nis` bağımsız MCP araçları değildir. Bunlar mevcut analiz, mütalaa, strateji, dilekçe ve kaynak arama akışlarına uzmanlık perspektifi ekleyen aktif yönlendirme lensleridir. Host uygulaması slash menüsünü destekliyorsa menüden, desteklemiyorsa doğal dille kullanılabilir.

## Sistem gereksinimleri ve güvenlik

Portable Windows x64 için yazma izni olan bir klasör ve internet bağlantısı (bağımlılıkların ilk indirilmesi için) yeterlidir. Kaynak kod yönteminde Python 3.11+ ve `uv` gerekir. API anahtarları kullanıcıya aittir; ücret, kota ve sağlayıcı veri politikası sağlayıcıya göre değişir. Tüm sonuçlar `analysis_only` ve `non_binding` niteliğindedir.

Lisans ve fork atıfları için [LICENSE](LICENSE) ve [NOTICE.md](NOTICE.md) dosyalarına bakın. Kurulum ayrıntıları için [portable rehberini](docs/socratlegal-user-install.md), IDE ayarları için [MCP istemci rehberini](docs/mcp-client-setup.md) okuyun.
