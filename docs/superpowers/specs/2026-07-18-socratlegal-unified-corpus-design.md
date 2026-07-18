# SocratLegal Birleşik Corpus ve Uzman Raporu Tasarım Belgesi

## Amaç

LegalAI'nin kamuya açık ürün adını SocratLegal olarak konumlandırmak; mevcut upstream istemcilerini tek bir LegalAI/SocratLegal MCP sunucusu altında birleştirmek; yerel corpus ile canlı resmi kurum adapter'larını aynı sorguda birlikte çalıştırmak; bütün analiz, karşı taraf, derin araştırma, strateji ve bilirkişi akışlarını birleşik kaynak katmanına bağlamak.

Yerel Python paketleri ve klasörleri geriye dönük uyumluluk için `legalai` olarak kalabilir. Kamuya açık MCP sunucu adı, IDE kaydı ve yeni tool/prompt/resource adları `socratlegal`/`SocratLegal` olur. Eski `legalai_*` adları geçiş süresince alias olarak korunur.

## Kullanıcı koşulları ve tasarım kararları

- Hosting, özel domain veya merkezi server zorunlu değildir.
- Yerel corpus ve resmi kurum API/site adapter'ları aynı anda aranır; yerel corpus tek başına öncelikli değildir.
- Yargıtay, Danıştay, AYM ve AİHM corpus olarak indirilmemiş olsa bile canlı Bedesten/resmi API/HUDOC araması her zaman korunur.
- Corpus oluşturma önceliği, veri ve adapter geliştirme sırasıdır; hukuki muhakemede kaynak üstünlüğü sırası değildir.
- Yerel corpus `.data/socratlegal_corpus.db` içinde tutulur ve Git'e gönderilmez.
- Upstream modülleri ayrı MCP server olarak çalıştırmak yerine ortak source adapter protokolüyle aynı LegalAI process'ine bağlanır.
- Her kaynak için erişim, atıf, bağlayıcılık, güncellik ve lisans durumu ayrı metadata olarak taşınır.
- Çıktılar `analysis_only` ve `non_binding` niteliğini korur.

## Kaynak mimarisi

```text
SocratLegal UnifiedSourceBackend
│
├── LocalCorpusAdapter
│   └── SQLite + FTS5; isteğe bağlı yerel semantic index
│
├── LiveSourceAdapters
│   ├── Bedesten/Yargıtay/Danıştay
│   ├── AYM
│   ├── HUDOC/AİHM
│   ├── Rekabet Kurumu
│   ├── KVKK
│   ├── KİK
│   ├── TİHEK
│   ├── Kamu Denetçiliği
│   ├── BDDK/SPK/BTK/RTÜK/EPDK/KGK/GİB
│   ├── Emsal/Sayıştay/Uyuşmazlık/Sigorta Tahkim
│   └── diğer resmi kurum adapter'ları
│
├── AcademicAndPolicyAdapters
│   ├── DergiPark, baro/TBB, YÖK tezleri
│   ├── Rekabet uzmanlık tezleri ve Rekabet Dergisi
│   ├── OECD
│   └── AB Komisyonu, ABAD/Genel Mahkeme, EUR-Lex, Curia
│
└── FederatedRetriever
    ├── kaynakları paralel sorgular
    ├── belge kimliği/hash ile deduplicate eder
    ├── source policy ve authority metadata ekler
    ├── canlı ve yerel sonuçları birlikte rerank eder
    └── her sonuç için provenance/atıf taşır
```

Her adapter şu sözleşmeye yaklaşır:

```python
class SourceAdapter(Protocol):
    source_id: str

    async def search(self, query: str, limit: int) -> list[Document]: ...

    async def fetch(self, document_id: str) -> Document | None: ...

    async def sync(self, cursor: str | None = None) -> SyncReport: ...
```

`SyncReport`, adapter'ın eklediği, güncellediği, atladığı ve hata aldığı belge sayılarını; yeni cursor değerini ve kaynak uyarılarını taşıyan küçük bir veri nesnesidir. Adapter'lar ağ üzerinden aldıkları ham modeli doğrudan analiz katmanına vermez; önce ortak `Document` ve provenance modeline dönüştürür.

FederatedRetriever canlı adapter başarısız olduğunda yerel sonucu kullanabilir; canlı sonuç geldiğinde yerel sonucu silmez. Aynı belgenin canlı ve yerel kopyası tek provenance kaydında birleştirilir. Kaynağın canlı olması otomatik olarak bağlayıcı veya üstün olduğu anlamına gelmez; hukuki otorite sınıflandırması ayrı katmanda yapılır.

## Corpus depolama

Varsayılan yerel dosya:

```text
<proje kökü>/.data/socratlegal_corpus.db
```

Önerilen tablolar:

- `source_registry`: kaynak, adapter, erişim ve sync politikası
- `corpus_documents`: belge kimliği, başlık, belge türü, kurum, tarih, URL, künye, metin hash'i
- `corpus_revisions`: belge sürümleri, yürürlük/durum değişiklikleri ve alınma tarihleri
- `corpus_chunks`: arama için metin parçaları ve başlık/section bilgileri
- `corpus_fts`: SQLite FTS5 indeks kayıtları
- `corpus_citations`: künye, kısa alıntı, sayfa/bölüm ve provenance
- `sync_cursors`: kaynak bazında son senkronizasyon konumu

Yargıtay/Danıştay/AYM/AİHM için tam corpus indirme varsayılan değildir. Bu kaynaklarda canlı adapter'lar temel veri yoludur; kullanıcı isterse seçili belgeleri yerel corpus'a sabitleyebilir. Rekabet Kurumu, KVKK, KİK, TİHEK ve Kamu Denetçiliği corpus'ları öncelikli sync kapsamına alınır.

## Corpus geliştirme önceliği

Bu sıra yalnızca adapter/corpus oluşturma sırasıdır:

1. Rekabet Kurumu kararları, mevzuat, tebliğ, yönetmelik, kılavuz, sektör raporları; OECD; AB Komisyonu/ABAD/Curia/EUR-Lex rekabet kaynakları
2. KVKK Kurul kararları, ilke kararları ve KVKK rehberleri
3. KİK kararları ve ilgili mevzuat
4. TİHEK kararları ve mevzuatı
5. Kamu Denetçiliği Kurumu kararları ve mevzuatı
6. BDDK, SPK, BTK, RTÜK, EPDK, KGK, GİB, Sayıştay, Emsal, Uyuşmazlık, Sigorta Tahkim ve diğerleri
7. Doktrin, tez, baro/TBB ve akademik kaynakların genişletilmesi

Hukuki değerlendirmede ise mevzuat, kararın bağlayıcılığı, yargı hiyerarşisi, kurum yetkisi, tarihsel yürürlük ve somut olayla ilişki ayrı ayrı analiz edilir. Corpus önceliği bu ayrımı değiştirmez.

## Arama ve analiz akışı

```text
Kullanıcı sorusu
    ↓
PII maskesi
    ↓
Persona/jurisdiction/lens seçimi
    ↓
Yerel corpus + canlı resmi adapter'lar (paralel)
    ↓
Normalize + deduplicate + source policy
    ↓
Rerank + provenance + citation extraction
    ↓
Temporal Legal Context
    ↓
Katmanlı analiz / agresif karşı taraf / deep research / strateji
    ↓
Host veya seçili server-side LLM sentezi
```

Yalnızca sonuç üretmeyen bir adapter `trace` ve `assumptions` alanlarına yazılır. Bir kaynağın aranamadığı durumda sistem bunu “kaynak yok” veya “aranamadı” şeklinde açıkça belirtir; başka kaynağın sonucu sanki o kuruma aitmiş gibi gösterilmez.

## Güncelleme ve hosting olmadan kullanım

Kullanıcı yerel corpus'u açıkça senkronize eder:

```powershell
uv run socratlegal corpus sync --source all
uv run socratlegal corpus sync --source rekabet
uv run socratlegal corpus status
```

Senkronizasyon URL, resmi kimlik, hash, yayın/yürürlük tarihi ve sürüm bilgisiyle artımlı çalışır. Canlı API veya site erişimi yoksa mevcut yerel corpus kullanılabilir; yeni kararlar ancak resmi kaynağa erişildiğinde veya kullanıcı belgeyi yerel olarak içeri aldığında eklenebilir. İsteğe bağlı Windows Task Scheduler entegrasyonu daha sonraki bir görevdir.

## Bilirkişi raporu itiraz üretim modülü

Modül iki ayrı MCP yeteneği sağlar:

- `socratlegal_bilirkisi_raporu_analiz`
- `socratlegal_bilirkisi_raporu_dilekce`

Girdi katmanı PDF, DOCX, XLSX, TXT, HTML ve görsel/OCR kaynaklarını yerel olarak ayrıştırır. Dosyanın tamamı dış servise gönderilmeden önce PII maskelenir; mümkünse teknik ayrıştırma yerel yapılır.

Üretim zinciri:

1. Raporun teknik bulgu, yöntem, veri, varsayım, hesap, tablo ve sonuçlarını çıkar.
2. İlgili mühendislik/bilim alanını algıla ve teknik uzman lensi ata.
3. Her rapor iddiası için teknik karşı argüman, alternatif yöntem ve veri/ölçüm itirazı üret.
4. Teknik itirazı bilirkişinin görev sınırları, ispat hukuku, usul, mevzuat ve içtihatla eşleştir.
5. Olay, rapor, dava ve diğer tarihler üzerinden Temporal Legal Context uygula.
6. Her itirazı “rapor bulgusu → teknik itiraz → hukuk kuralı → kaynak → delil/isteme → dilekçe paragrafı” olarak göster.
7. Belirsiz teknik meseleleri kesin hüküm gibi sunma; insan teknik uzmanı ve avukat denetimini zorunlu uyarı olarak ekle.

Gemini, Claude veya başka host modelin kendi dosya/teknik analiz yeteneği bu modülün yerine geçmez; bu modülün farkı, teknik incelemeyi SocratLegal corpus, atıf, temporal context ve yapılandırılmış hukuk çıktısıyla birleştirmesidir.

## SocratLegal marka ve IDE geçişi

- FastMCP görünen adı `SocratLegal MCP Server` olur.
- Yeni MCP kaydı `socratlegal` olur.
- Yeni public tool/prompt/resource isimleri `socratlegal_*` olur.
- Eski `legalai_*` isimleri geçiş alias'ı olarak korunur.
- Yerel `legalai` Python package ve klasör adları korunabilir.
- Cursor'da mevcut `yargi-mcp-fork` kaydı silinmez; yalnızca mevcut `legalai` kaydı `socratlegal` adıyla ayrı bir kayıt olarak güncellenir.
- Codex, Claude, Antigravity ve VS Code dokümanları aynı public adı kullanır.

## Güvenlik ve lisans sınırları

- Upstream client adapter'ları LegalAI process'ine alınmadan önce hard-coded dış servis anahtarları kaldırılıp `.env` ayarlarına taşınır.
- Kullanıcı PII'si dış API/LLM çağrısından önce maskelenir.
- Doktrin, OECD, yabancı karar ve akademik içerik bağlayıcı hukuk gibi sunulmaz.
- Tam metin saklama ve alıntı uzunluğu kaynak lisansı/erişim politikasına göre sınırlanır.
- `.data/` corpus dosyaları Git'e eklenmez; upstream reposuna hiçbir veri veya commit gönderilmez.

## Kapsam dışı bırakılanlar

- Merkezi hosting veya özel domain kurulumu
- Tüm kaynakların zorunlu tam aynasının her kullanıcıya indirilmesi
- Lisanslı veri sağlayıcılarının lisans şartlarını aşan toplu kopyalama
- Teknik bilirkişi görüşünün gerçek uzman veya mahkeme kararı yerine geçirilmesi
