# SocratLegal Sözleşme İnceleme, Muhakeme ve Güncelleme Tasarımı

## Amaç

SocratLegal'e, yerel çalışan MCP mimarisini ve upstream modüllerini bozmadan,
kaynaklı ve izlenebilir bir sözleşme inceleme yeteneği eklemek. Modül sözleşmenin
gerçek hukuki niteliğini, ilgili persona ve sektör bağlamlarını, riskli/eksik
hükümleri, karşı görüşleri ve revizyon önerilerini değerlendirir. Yabancı dildeki
sözleşmeler için Türkçe açıklama ile birlikte kaynak dilinde hukuk terminolojisine
uygun öneri metni üretir.

Bu tasarım due diligence uygulamasını kapsamaz.

## Gizlilik ve örnek mütalaa sınırı

Kullanıcının sağladığı mütalaa ve uzman görüşleri eğitim verisi, yerel corpus
veya Git deposu olarak saklanmayacaktır. Onlardan çıkarılan genel yöntem, ham
olay, taraf, belge veya isim içermeyen bir `ReasoningPlaybook` politikası olarak
kodlanacaktır. Bu politika; soru/sınır belirleme, vakıa-kronoloji-belge ayrımı,
norm-unsur-somut olay eşleştirmesi, karşı görüş, ara sonuç ve kaynaklı nihai
sentez sırasını tarif eder.

SocratLegal'in başlattığı her dış arama veya isteğe bağlı server-side LLM çağrısı
öncesinde metin yerelde maskelenir. Sözleşme modülü için yapılandırılmış PII
maskesine ek olarak taraf/adres/iletişim ve kimlik bağlamını daha güvenli yer
tutuculara dönüştüren bir `ContractPrivacyGate` uygulanır. Ham sözleşme metni,
maskelenmemiş alıntı, API anahtarı ve eşleştirme haritası loglara, release paketine
veya corpus'a yazılmaz.

MCP hostu kullanıcının belgeyi veya sohbetini SocratLegal çağrısından önce
görüyorsa, o host/sağlayıcının veri politikası SocratLegal tarafından kontrol
edilemez. Bu sınır hem araç açıklamasında hem de sonuçta şeffaf biçimde gösterilir.

## Ortak muhakeme ve operasyonel bağlam

Mevcut dört aşamalı hukuki muhakeme, aşağıdaki ortak akışla genişletilir:

1. Hukuki soru, talep, vakıa, belge, tarih ve belirsizlikleri ayır.
2. Normatif çerçeveyi, unsurları, emredici hükümleri, temporal context'i ve kaynak hiyerarşisini belirle.
3. Somut olayları hukuki unsurlarla; ilgili operasyon, iş akışı, sektör, pazar, teknik veya davranışsal bağlamla birlikte eşleştir.
4. Lehe/aleyhe görüşleri, çözüm yollarını, riskleri, doğrulanması gereken olguları, kısa yönetici özetini ve detaylı kaynaklı analizi ver.

`OperationalContextBuilder`, hukuk dışı bağlamı yalnızca ilgili olduğu ölçüde
ekler. Örneğin IBAN/kripto dolandırıcılığında işlem akışı, olası fail
motivasyonları ve zarar mekanizmaları; ticari sözleşmede ürün/hizmet, sektör,
tedarik/dağıtım akışı ve pazar teamülleri değerlendirilir. Bu katman hiçbir zaman
ispatlanmış maddi vakıa yerine geçmez: her tespit `operasyonel hipotez`,
`kullanıcı beyanı`, `belgeyle desteklenen olgu` veya `doğrulama gerekli`
etiketlerinden birini taşır.

Yalnızca erişilmiş kaynaklardan mevzuat maddesi, karar künyesi, eser/makale
künyesi veya kısa alıntı gösterilir. LLM'in genel bilgisinden gelen operasyonel
yorum kaynak yoksa açıkça kaynaklandırılmamış hipotez olarak belirtilir.

## Sözleşme inceleme akışı

```text
Sözleşme metni/dosyası
  -> yerel gizlilik kapısı ve metin çıkarma
  -> intake: taraf, sıfat, tarih, dil, yabancılık, edim ve belge kalitesi
  -> nitelendirme: tipik, atipik veya karma sözleşme; baskın unsur haritası
  -> persona router: çağrılan/çağrılmayan profil ve negatif gerekçe
  -> bağımsız uzman incelemeleri + operasyonel bağlam
  -> kaynak/federated retrieval + temporal legal context
  -> çelişki çözümü, gap/risk taraması ve madde bazlı revizyon
  -> yönetici özeti + ayrıntılı kaynaklı rapor
```

### Intake ve nitelendirme

Intake; tarafların gerçek/tüzel kişi niteliğini, tacir-tüketici-kamu-finansal
kuruluş sıfatlarını, sözleşmenin dilini, para/ifa yerini, veri işleme ve
yabancılık unsurlarını çıkarır. Başlık yerine içeriği esas alarak TBK m. 19
bağlamında tavsif kontrolü yapar. Tipik, karma ve sui generis olasılıkları;
baskın unsur/absorbsiyon, kombinasyon ve TBK genel hükümleri seçenekleriyle
birlikte sunulur.

### Persona router

Router mevcut hukuk, ceza, idare, vergi, rekabet, KVKK, KİK, sigorta,
anayasa/insan hakları ve sektörel lensleri kullanır. KVKK, rekabet, tahkim,
fikri mülkiyet, iş, tüketici, finans/BDDK-SPK, sigorta, enerji, kamu ihale,
gayrimenkul/inşaat ile MÖHUK için belirlenebilir tetikleyiciler tanımlanır.

Her profil için `PersonaRouteDecision` üretilir:

- `selected`: İncelemeye katılıp katılmadığı.
- `positive_triggers`: Katılma sebepleri.
- `negative_reason`: Katılmadıysa zorunlu, kullanıcıya açık gerekçe.
- `priority`: MÖHUK gibi çerçeve belirleyen veya destekleyici rolü.
- `confidence` ve `verification_needed`.

Yabancılık unsuru varsa MÖHUK ilk sırada uygulanacak hukuk, emredici/doğrudan
uygulanan kural, lex causae/lex arbitri ve tanıma-tenfiz filtresini kurar. Diğer
persona bulguları bu çerçeveyle etiketlenir.

### Madde bazlı bulgular

Her `ClauseFinding` şunları içerir:

- madde kimliği/metni veya güvenilir konum işareti;
- tespit, risk seviyesi ve neden;
- nitelendirme/statü uyarısı (ör. acente-bayii veya işçi-bağımsız yüklenici);
- mevzuat, içtihat, kurum kararı ve doktrin için ayrı künye/otorite bilgisi;
- karşı görüş ve belirsizlik;
- operasyonel bağlam etiketi;
- mevcut metnin korunması, değiştirilmesi veya ek hüküm önerisi;
- eksik olgu ve doğrulama adımı.

Evrensel boşluk taraması; gizlilik, mücbir sebep, fesih, devir/temlik,
uygulanacak hukuk, yetki/tahkim, bildirim, bütünlük, kısmi geçersizlik ve gerekli
ise delil sözleşmesini kapsar. Sözleşme türüne özel kontroller, tespit edilen
türün gerektirdiği ayrı kontrol listelerinden eklenir.

İlk persona değerlendirmeleri birbirini ankrajlamamak için bağımsız üretilir.
Sentez katmanı çelişkileri gizlemez; emredici normun ticari tercih karşısındaki
önceliğini açıklar ve alternatif sonuçları birlikte raporlar.

### Yabancı dil ve çift dilli revizyon

Kaynak sözleşme Türkçe değilse her öneri şu sırayla gösterilir:

1. Türkçe açıklama: sorun, hukuki neden, risk ve varsayım.
2. Kaynak dilinde önerilen hüküm: LLM'in genel dil kapasitesiyle hukuki terminolojiye uygun taslak.
3. Türkçe karşılık: önerilen yabancı dil hükmünün hukuki anlam kontrolü için.

Bu metinler yeminli/sertifikalı çeviri veya kesin hukuk görüşü olarak sunulmaz.
Kaynak dil güvenle algılanamazsa sistem bu belirsizliği belirtir ve kullanıcıdan
doğrulama ister.

## MCP yüzeyi ve çıktı sözleşmesi

Yeni genel araç adı `socratlegal_sozlesme_incele` olacaktır; geriye uyumluluk
için `legalai_sozlesme_incele` alias'ı eklenir. Girdi, doğrudan `contract_text`
veya yerel `file_path`, amaç/pozisyon, tercih edilen çıktı ayrıntısı, varsa
olay-tarih bağlamı ve isteğe bağlı `jurisdiction_hint` içerir.

`file_path`, yerel `.txt`, `.md`, `.pdf` ve `.docx` belgelerini kabul eder.
Taranmış veya görüntü tabanlı PDF'de yerel OCR eklentisi veya işletim sistemi OCR
motoru kullanılamıyorsa sonuç açıkça
`ocr_required` uyarısı verir; belge kalıcı olarak saklanmaz.

Araç, API anahtarı olmadan yapılandırılmış bulgular, kaynak paketleri, persona
kararları ve host modelin nihai raporu yazması için talimat döndürür. İsteğe
bağlı API anahtarı varsa aynı sonuç server-side sentezle de üretilebilir. Host
modeli hiçbir zaman erişilmeyen karar, madde, eser veya alıntıyı uydurmaya yetkili değildir.

Nihai görünüm: kısa yönetici özeti; sözleşme niteliği/uygulanacak hukuk; persona
karar tablosu; madde bazlı bulgular; boşluk analizi; nitelendirme uyarıları;
revizyon önerileri; karşı görüşler; kaynakça; varsayımlar ve non-binding uyarısıdır.

`socratlegal_yardim` ve `legalai://capabilities`, sözleşme inceleme yeteneğini
aktif araç olarak gösterir; kullanıcı doğal dilde istem yazsa dahi hostun bu aracı
seçebilmesi için örnek istemler eklenir.

## API ve IDE kullanım modeli

Host-abonelik modu; Codex/ChatGPT, Cursor, Claude, Antigravity ve uygun VS Code
MCP istemcisinin kendi modelini nihai metin için kullanmasıdır. SocratLegal bu
modda ayrıca sağlayıcı anahtarı istemez; IDE'nin abonelik kimliği MCP sunucusuna aktarılmaz.

Server-side sentez modu, yalnız kullanıcının kendi yerel ortamında verdiği
anahtarla çalışır. Mevcut somut sağlayıcılar Gemini, DeepSeek, Groq ve
OpenRouter'dır; model adı ilgili yerel yapılandırma değişkeniyle seçilir.
OpenRouter üzerinden sağlayıcının sunduğu model seçilebilir. Ayarlarda bulunan
ama router'a bağlı olmayan OpenAI/Anthropic alanları, bu sürümde destekleniyor
gibi gösterilmeyecek; ayrı sağlayıcı adaptörü eklenmeden kullanılmayacaktır.

## Güncelleme ve dağıtım

Mevcut portable güncelleme altyapısı, yerel manifest/arşiv ile checksum doğrulama
ve rollback yapar. Bu kapsamda aşağıdaki eksik kullanıcı deneyimi tamamlanır:

- GitHub Releases'teki platforma özel manifest, yalnız açık kullanıcı isteğiyle HTTPS üzerinden sorgulanır.
- `socratlegal_guncelleme_kontrol` aracı ve CLI karşılığı, en fazla 24 saatte bir metadata kontrolü yapar; belge metni veya kullanıcı verisi göndermez.
- Yeni sürüm varsa araç sürüm notu/indirme hedefi sunar; otomatik uygulama yapmaz.
- `socratlegal update apply` arşivi geçici dizine indirir, SHA-256 doğrular, yalnız `app` katmanını değiştirir, `app.previous` yedeğini tutar ve başarısız sağlık kontrolünde geri döner.
- `data`, yerel corpus, PII haritası, API anahtarları ve IDE JSON/TOML kayıtları güncelleme dışında tutulur.

Kaynak checkout kullanan kullanıcı için güncelleme `git pull`, `uv sync --frozen`
ve IDE/MCP yeniden başlatmasıdır; yeniden JSON kurulumu gerekmez.

## Sınırlar

- Yeni hosting, uzak MCP runtime veya özel domain kurulmaz.
- Due diligence tasarlanmaz veya uygulanmaz.
- Ham örnek mütalaalar, kullanıcı sözleşmeleri ve kişisel veriler corpus'a, Git'e, telemetry'ye veya release paketine konmaz.
- LLM genel bilgisi bağlayıcı hukuk, doğrulanmış olgu veya kaynak yerine geçmez.
- Çıktılar analysis-only, non-binding ve insan uzman incelemesine tabidir.

## Doğrulama ölçütleri

- Özel örnek belgelerin dosya adı/ham metni repo içinde yer almaz.
- Muhakeme politikası dört aşamalı analizi, karşı görüşü, kaynak türlerini ve ayrıntılı + özet çıktı kuralını üretir.
- Operasyonel bağlam, ispatlanmış vakıadan ayrı etiketlenir.
- Router, seçilmeyen tetiklenebilir personada negatif gerekçe üretir; MÖHUK yabancılık unsurunda üst katman olur.
- Karma/atipik tavsif, acente-bayii ve işçi-bağımsız yüklenici uyarıları test edilebilir yapılandırılmış bulgular verir.
- Yabancı dil sözleşmede çift dilli öneri, dil belirsizliği ve çeviri uyarısı görünür.
- Her doğrulanabilir hukuki iddia yalnız erişilmiş kaynağa bağlanır; erişilmemiş kaynağa künye veya alıntı uydurulmaz.
- API anahtarsız host modu ve isteğe bağlı server-side sentez birlikte çalışır.
- Güncelleme kontrolü kullanıcı onayı olmadan indirme/uygulama yapmaz ve kullanıcı verisini korur.
