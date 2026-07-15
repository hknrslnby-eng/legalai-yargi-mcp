# Hafta 9 Agresif Karşı Taraf Tasarım Belgesi

## Amaç

`FORK-KAPSAMLI-PLAN.md` Hafta 9 kapsamındaki `agresif_karsi_taraf` modülünü, ayrı bir hosting veya zorunlu sunucu API anahtarı gerektirmeden Codex, Cursor, Claude ve Gemini aboneliği kullanan Antigravity gibi MCP hostlarında çalıştırmak. API anahtarı bulunan kullanıcılar için OpenRouter, DeepSeek, Gemini ve mevcut Groq uyumlu istemci yolu üzerinden sunucu-tarafı üretimi de açık bırakılacaktır.

Başarı ölçütü: Davacı pozisyonu gibi bir girdi, host-orchestrated modda host modele açıkça 5 karşı argüman ve zayıf nokta analizi ürettirecek talimatları ve gerçek arama sonuçlarını; server-synthesized modda ise doğrudan 5 karşı argüman, zayıf noktalar ve en fazla 3 rebutting kararını döndürür.

## Kapsam

### Dahil

- `OpposingRoleMap`: kullanıcı rolünü hukuki karşı role çeviren saf bileşen.
- `RedTeamCounterArgs`: 5 karşı argüman üretimi veya anahtarsız modda 5 yapılandırılmış üretim talimatı.
- `RebuttingCaseSearch`: karşı argüman sorgularıyla Bedesten backend'inde arama, belge kimliğine göre tekilleştirme ve en fazla 3 karar.
- `WeakPointDetector`: pozisyonun zayıf yönlerini server LLM ile veya host model için talimat olarak üretme.
- `run_opposing(...)` domain fonksiyonu.
- MCP `agresif_karsi_taraf` aracı ve `POST /api/v1/opposing` adaptörü.
- `ENABLE_AGGRESSIVE_OPPOSING` feature flag'i.
- Yapılandırılabilir OpenRouter ve DeepSeek sağlayıcı/model seçimi.
- Repo kapsamlı Codex MCP yapılandırması ve çoklu istemci kurulum dokümantasyonu.
- Dış ağa ve gerçek LLM'e ihtiyaç duymayan birim, adaptör ve kabul testleri.

### Hariç

- Yeni bir web arayüzü, veritabanı veya ayrı hosting kurulumu.
- LLM sağlayıcılarının model adlarını kalıcı olarak kod içine kilitlemek.
- Hukuki tavsiye, dava sonucu tahmini veya kararların kesin emsal olduğu iddiası.
- Antigravity'ye özel kapalı API entegrasyonu. Destek, standart yerel stdio MCP sunucusu ve host model akışı üzerinden sağlanır.

## Mimari

```text
position + role + jurisdiction
        |
        v
OpposingRoleMap
        |
        v
RedTeamCounterArgs
        |
        +--> RebuttingCaseSearch --> BedestenSearchBackend
        |
        v
WeakPointDetector
        |
        v
OpposingResult
```

MCP ve HTTP katmanları yalnızca giriş doğrulama, feature flag kontrolü ve domain sonucunu dış şemaya dönüştürür. İş mantığı `legalai/packages/layers/` altında kalır. Böylece ileride remote MCP veya web UI eklendiğinde aynı domain akışı kullanılabilir.

## Çalışma modları

### Host-orchestrated

Sunucu tarafında uygun API anahtarı yoksa `run_opposing` LLM çağrısı yapmaz. Bunun yerine:

1. Rol eşleştirmesini yapar.
2. Beş standart karşı argüman ekseni için host modelin dolduracağı yapılandırılmış talimatları üretir.
3. Pozisyon ve eksen sorgularıyla gerçek kararları arar.
4. Host modele, beş karşı argümanı, zayıf noktaları ve yalnızca dönen belge kimlikleriyle kaynaklandırılmış rebuttal raporunu yazmasını söyleyen `assistant_instructions` döner.

Bu yol Codex/ChatGPT, Claude, Cursor ve Gemini aboneliği kullanan Antigravity için ek sunucu anahtarı gerektirmez.

### Server-synthesized

Sağlayıcı anahtarı ve model yapılandırılmışsa:

1. `LLMRouter` üzerinden reasoning görevi için seçilen sağlayıcı çağrılır.
2. Karşı argümanlar tam olarak 5 kayıt halinde üretilir.
3. Her argüman ve pozisyon, rebutting karar aramasına sorgu girdisi olur.
4. Aynı sağlayıcı veya seçilebilir reasoning sağlayıcısı zayıf noktaları üretir.
5. Çıktı belge kimlikleriyle sınırlandırılır ve hukuki tavsiye uyarısı eklenir.

Sağlayıcı seçimi `LEGALAI_LLM_PROVIDER=auto|gemini|openrouter|deepseek|groq` ile yapılır. OpenRouter için `OPENROUTER_API_KEY` ve `OPENROUTER_MODEL`, DeepSeek için `DEEPSEEK_API_KEY` ve `DEEPSEEK_MODEL` kullanılır. Model adı env'den geldiği için DeepSeek v4 Pro veya OpenRouter'daki güncel modeller, kod değişmeden seçilebilir. Base URL'ler sağlayıcı varsayılanlarıyla gelir ve testlerde override edilebilir.

## Rol eşleştirme sözleşmesi

`OpposingRoleMap` aşağıdaki açık eşleşmeleri kullanır:

| Kullanıcı rolü | Karşı rol |
|---|---|
| `davacı` | `davalı` |
| `davalı` | `davacı` |
| `sanık` | `katılan/şikâyetçi ve iddia makamı` |
| `katılan` | `sanık` |
| `başvurucu` | `idare/karşı kurum` |
| `idare` | `başvurucu` |
| `karşı_taraf` | `pozisyonun karşı tarafı` |

Bilinmeyen rol reddedilmez; `opposing_role` değeri `karşı taraf` olarak döner ve `mapping_note` alanında rolün açık belirtilmesi gerektiği yazılır. Bu eşleştirme bir hukuki nitelendirme değil, red-team arama yönüdür.

## Sonuç şeması

Domain sonucu aşağıdaki alanları taşır:

```text
OpposingResult
  question: str
  position: str
  role: str
  opposing_role: str
  jurisdiction_id: str | None
  mode: "disabled" | "host_orchestrated" | "server_synthesized"
  counter_args: list[CounterArgument]       # host modunda prompt kayıtları, server modunda üretimler
  weak_points: list[WeakPoint]
  rebutting_cases: list[CaseSummary]        # en fazla 3, id'ye göre tekil
  sources: list[CaseSummary]
  assistant_instructions: str | None
  trace: list[dict[str, Any]]
  note: str
```

Her `CounterArgument` `id`, `title`, `content`, `mode` ve `supporting_query` alanlarını taşır. Her `WeakPoint` `id`, `issue`, `explanation` ve `mode` alanlarını taşır. `CaseSummary` en az `doc_id`, `citation`, `source` ve `relevance_query` alanlarını taşır. Host modunda `content` ve `explanation`, host modelin tamamlayacağı açık talimatlardır; bu nedenle sonuç yine 5 argüman kaydı taşır fakat bunlar sunucu üretimi olarak etiketlenmez.

## Feature flag ve hata davranışı

- `ENABLE_AGGRESSIVE_OPPOSING=false`: hiçbir LLM veya belge backend çağrısı yapılmaz; `mode="disabled"`, boş listeler ve kullanıcıya açık kapatma notu döner.
- Karar araması başarısız olursa hata `trace` içine yazılır; sonuç boş `rebutting_cases` ile devam eder.
- Server LLM çağrısı yapılandırılmamışsa otomatik host moduna geçilir.
- Server LLM çağrısı çalışma sırasında başarısız olursa mevcut kararlar korunur ve sonuç host talimatlarıyla `host_orchestrated` olarak döner.
- Üretilen veya host tarafından yazılan kaynaklar yalnızca arama sonucundaki `doc_id` değerleriyle sınırlandırılır. Geçersiz bir kaynak id'si varsa doğrulama ipucu üretilir.
- Her modda sonuç, bunun hukuki tavsiye değil araştırma/red-team taslağı olduğunu belirtir.

## MCP ve çoklu istemci kurulumu

`legalai/apps/mcp/server.py` içinde MCP sunucusunun genel `instructions` alanı, karşı taraf akışının sırasını, kaynaklandırma kuralını, API anahtarı olmadan host-orchestrated çalışma biçimini ve hukuki uyarıyı anlatır. Araç `readOnlyHint=true`, `openWorldHint=true`, `idempotentHint=true` anotasyonlarıyla kayıt edilir; dış sistemlere yazmaz.

Repo kapsamlı `.codex/config.toml`, sırları içermeden `uv run legalai-mcp` stdio komutunu `legalai` adıyla kaydeder. Codex desktop, CLI ve IDE aynı Codex yapılandırma katmanını paylaşır; config yenilendikten sonra Codex yeniden başlatılır veya yeni bir task açılır. Antigravity için aynı komut, çalışma dizini ve `legalai` adı, istemcinin standart yerel MCP ayarına uyarlanır. Gemini aboneliği host model olarak kalır; MCP sunucusu Gemini API anahtarını zorunlu kılmaz.

Codex ve Cursor kayıtları birbirinden bağımsızdır: Codex yalnızca `.codex/config.toml` üzerinden, Cursor mevcut `.cursor/mcp.json` üzerinden çalışır. Kurulum sırasında Cursor dosyası, `yargi-mcp-fork` kaydı, kullanıcı ayarları veya sırlar üzerine yazılmaz; ortak TCP portu/global daemon kullanılmaz. Claude, VS Code ve Antigravity örnekleri de aynı çakışmasız yerel STDIO sözleşmesini izler. Doğrulama, iki config'in ayrı ayrı parse edilmesini ve mevcut Cursor içeriğinin değişmediğinin kontrolünü kapsar.

## Test tasarımı

Tüm yeni testler sahte router ve enjekte edilebilir sahte `DocumentSearchBackend` kullanır:

1. Rol eşlemelerinin tamamı ve bilinmeyen rol fallback'i.
2. Host modunda 5 prompt argümanı, host talimatı ve 3 tekil karar.
3. Server modunda sahte LLM ile tam 5 argüman ve zayıf nokta çıktısı.
4. Aynı belge farklı sorgulardan dönünce tekilleştirme ve 3 belge sınırı.
5. Feature flag kapalıyken router/backend çağrısının yapılmaması.
6. LLM yapılandırılmamış ve LLM çalışma zamanı hatası fallback'leri.
7. MCP aracının ortak domain fonksiyonunu doğru parametrelerle çağırması.
8. `/api/v1/opposing` request/response sözleşmesi.
9. Davacı pozisyonu kabul testi: sonuçta 5 karşı argüman kaydı ve 3 rebutting karar bulunması.

Gerçek Bedesten, OpenRouter, DeepSeek veya Gemini çağrısı test paketinin parçası değildir; bunlar ayrıca manuel smoke test olarak dokümante edilir.

## Revizyon: zamansal hukuk bağlamı ve geniş çözüm stratejisi

Hafta 9, yalnızca karşı tarafın argümanlarını üretmez. `TemporalLegalContext` ve `StrategicPathPlanner` ortak domain bileşenleri olarak normal QA, derin araştırma, katmanlı analiz ve agresif karşı taraf yüzeylerinde kullanılabilir.

### TemporalLegalContext

`TemporalLegalContext`, kullanıcı metninden birden fazla tarih gözlemi çıkarır ve her gözlemi kaynağı, kesinlik seviyesi ve kullanıcı tarafından doğrulanıp doğrulanmadığıyla saklar:

- olay, zarar, öğrenme, temerrüt, fesih ve sona erme tarihi;
- tebliğ, başvuru, ret, dava, icra, karar ve ödeme tarihi;
- mevzuatın yürürlük, değişiklik, yürürlükten kalkma ve geçiş tarihi;
- AYM iptal kararının Resmî Gazete tarihi ve varsa ertelenmiş yürürlük tarihi;
- Danıştay veya idari yargı kararının etkili olduğu kabul edilen tarih.

Tarih kesin değilse sistem kesin sonuç üretmez. `date_observation`, `confidence`, `assumption`, `missing_dates` ve `scenario_id` alanlarıyla algılanan tarihi, kullanıcının doğrulaması gereken tarihi ve bu tarihin sonucu nasıl değiştirdiğini ayrı gösterir. Tarih hiç yoksa modül durmaz; `current_law_baseline` modunda güncel mevzuata göre olası yolları sunar ve tarihsel yürürlük sonucu vermediğini belirtir.

`LimitationAndPreclusionAnalyzer`, zamanaşımı, hak düşürücü süre, dava şartı süresi, idari başvuru süresi, itiraz/istinaf/temyiz süresi ve icra itiraz sürelerini; süreyi başlatan, kesen, durduran veya etkileyen olaylarla birlikte adaylar halinde hesaplar. Her süre `start_event`, `candidate_deadline`, `legal_basis`, `interruptions`, `suspensions`, `confidence` ve `verification_needed` alanlarını taşır.

### StrategicPathPlanner

Strateji, varsayılan olarak “dava aç” sonucuna indirgenmez. Kullanıcının hedefi tahsilat, ihlalin durdurulması, delilin korunması, ikrar/kabul alınması, resmi kayıt oluşturulması, hızlı-gizli çözüm veya pazarlık gücü kazanılması olarak modellenir. Olayın niteliğine göre ihtar, noter tespiti, delil tespiti, Avukatlık Kanunu m.35/A uzlaşması, sulh/feragat/ibra/borç yapılandırması, ihtiyari veya dava şartı arabuluculuk, dava, icra, ihtiyati haciz/tedbir, somut suç şüphesi varsa ceza şikâyeti/ihbarı, idari başvuru/itiraz, düzenleyici kurum/kurul, tüketici hakem heyeti, KİK, Rekabet Kurumu, KVKK, tahkim ve alana özgü diğer yollar taranır.

Ceza yolu yalnızca somut suç ihtimali varsa önerilebilir; süreç delil elde etmek için kötüye kullanılmamalı ve bu risk açıkça gösterilmelidir. Her `StrategyOption` `objective`, `sequence`, `preconditions`, `forum_candidates`, `mandatory_prerequisites`, `deadline_risks`, `limitation_risks`, `evidence_gain`, `opponent_response`, `cost`, `confidentiality`, `irreversibility`, `enforceability`, `risks`, `parallel_paths`, `stop_conditions` ve `verification_needed` alanlarını taşır.

### ForumAndDeadlineAnalyzer

Her strateji yolu için görevli mahkeme, yetkili mahkeme ve alternatif yetki noktaları, görevli icra dairesi ve takip türü, görevli kurum/kurul, zorunlu ön başvuru veya arabuluculuk, dava şartı, zamanaşımı ve hak düşürücü süre riskleri ayrı `ForumCandidate` kayıtlarıyla üretilir. Sistem tek ve kesin bir merci seçmek yerine olayın ticari/tüketici/iş/idari niteliği, taraf sıfatı, yerleşim yeri, ifa yeri, taşınmaz yeri, önceki dava/icra ve başvurulara göre sıralı ihtimalleri gösterir.

Her `ForumCandidate` şu alanları taşır: `path`, `authority`, `legal_basis`, `jurisdiction_reason`, `alternative_forums`, `mandatory_prerequisites`, `limitation_risk`, `preclusion_risk`, `procedural_deadline_risk`, `supporting_evidence`, `confidence` ve `verification_needed`.

### Kaynak ve IDE çıktı kuralı

Projenin tüm yüzeylerinde `EvidenceBlock` varsayılan olarak üretilir:

```text
EvidenceBlock
  claim
  source_type: mevzuat | içtihat | doktrin | resmi açıklama
  citation_key
  full_citation
  short_quote
  source_url_or_document_id
  temporal_status
  relevance_to_fact
  confidence
```

Her normatif öneri, süre görüşü, görev/yetki görüşü, strateji seçimi ve karşı argüman ilgili `EvidenceBlock` ile aynı bölümde gösterilir. IDE/host çıktısında kaynaklar yalnızca sonda listelenmez; ilgili cümlenin yanında kaynak türü ve künye ile görünür. Arayüz varsayılan olarak kısa ilgili pasajı ve künyeyi açık gösterir; tam belge bağlantısı/kimliği genişletilebilir kaynak kartında bulunur. Kaynak bulunamazsa çıkarım `kaynaklandırılmamış çıkarım` diye etiketlenir ve hukuki dayanak gibi sunulmaz.

### Bağlayıcılık ve kesinlik kuralı

Alternatif kaynaklar, birden fazla içtihat veya doktrin görüşü bulunsa bile LegalAI çıktısı yalnızca araştırma ve değerlendirme taslağıdır; bağlayıcı hukuki görüş, kesin süre hesabı, resmi merci kararı veya hukuki sonuç garantisi değildir. Çelişen kaynaklar saklanmaz; görüş ayrılığı, kaynak hiyerarşisi, tarihsel geçerlilik ve doğrulanması gereken noktalar ayrı gösterilir. `confidence` alanı kaynak sayısının yerine geçmez ve yüksek güven bile bağlayıcılık anlamına gelmez.

### Kaynak kapsamı

İstek `source_scope=targeted|all|selected` alır. `targeted` ilgili yargı türü ve kurumları önceliklendirir; `all` yapılandırılmış tüm veri tabanı modüllerini tarar; `selected` kullanıcı tarafından seçilen kurum/kurul/veri tabanlarıyla sınırlar. Her modül arama maliyeti ve kapsanmayan kaynakları `trace` içine yazar.

## Revizyon test ve kabul kriterleri

Yeni testler sahte belge, mevzuat, karar ve doktrin sağlayıcılarıyla dış ağ olmadan çalışır:

1. Tarih gözlemleri; kesin, yaklaşık, çelişkili ve tamamen eksik girişlerde doğru güven/varsayım alanlarını üretir.
2. Tarih eksikken `current_law_baseline` çalışır; tarihsel yürürlük veya kesin süre iddiası üretmez.
3. AYM iptalinin Resmî Gazete tarihinde etkili olması ve ertelenmiş yürürlük senaryosu ayrı sonuç verir.
4. Zamanaşımı ve hak düşürücü süre adayları, başlangıç/kesilme/durma olayları ve doğrulama notuyla döner.
5. Aynı olay için dava, icra, 35/A, sulh/ibra, ihtiyari/dava şartı arabuluculuk, idari/kurul ve delil yollarından en az üç uygulanabilir seçenek sahte kaynaklarla üretilir.
6. Görevli/yetkili mahkeme, icra dairesi veya kurum/kurul için tek kesin cevap yerine sıralı `ForumCandidate` kayıtları ve sonucu değiştiren olgular döner.
7. Her strateji seçeneği en az bir `EvidenceBlock` taşır; kaynak yoksa `kaynaklandırılmamış çıkarım` etiketi kullanılır.
8. Çelişen içtihat veya doktrin görüşleri gizlenmez; kaynak hiyerarşisi ve görüş ayrılığı çıktıda görünür.
9. Host ve server modlarında bağlayıcı/kesin görüş uyarısı bulunur; `confidence=high` bile bağlayıcılık olarak yorumlanmaz.
10. `source_scope=targeted|all|selected` seçimleri doğru sağlayıcıları çağırır ve kapsamı trace'e yazar.

## Gelecek özellikler: sözleşme inceleme ve due diligence

Bu özellikler Hafta 9 kabul işinin parçası değildir; mevcut ortak altyapının sonraki kullanıcıları olarak planlanmıştır.

### Sözleşme inceleme

`ContractReview` modülü; sözleşme maddelerini taraf, yükümlülük, süre, yenileme, fesih, bedel, teminat, cezai şart, sorumluluk, mücbir sebep, veri işleme, yetki/uyuşmazlık çözümü ve risk başlıklarına ayırır. Her bulgu ilgili yürürlükteki mevzuat, içtihat ve veri tabanında varsa doktrinle kanıtlanır; değişiklik önerisi, risk seviyesi ve gerekçe birlikte gösterilir. Sözleşmenin imza, ifa, fesih ve uyuşmazlık tarihleri `TemporalLegalContext` ile değerlendirilir.

### Due diligence

`DueDiligence` modülü; hedef şirket/varlık/işlem hakkında yüklenen belgeler, seçili veri tabanları ve gerektiğinde tüm kaynaklar üzerinden hukuki risk envanteri çıkarır. İnceleme mülkiyet ve takyidat, dava/icra, sözleşmeler, izin/lisans, çalışanlar, vergi ve kamu borçları, KVKK, fikri mülkiyet, düzenleyici kurumlar, teminatlar, ilişkili taraflar, uyuşmazlık çözüm hükümleri ve kapanış önkoşullarını kapsar. Her risk `severity`, `likelihood`, `financial_or_operational_impact`, `missing_document`, `remediation`, `transaction_condition` ve kanıt bloklarıyla raporlanır.

## Tasarım girdileri ve rakip ürün gözlemleri

Kamuya açık ürün anlatımları yalnızca tasarım girdisi olarak kullanılmıştır; hiçbir ürün iddiası LegalAI için doğruluk veya kalite garantisi değildir. Argüman AI mevzuat, süre hesaplama ve kronolojik içtihat modüllerini; De Jure kaynaklı derin araştırma ve belgeye dayalı raporlamayı; Judis AI Resmî Gazete takibi, yasal süreler ve dava operasyonlarını; Apilex risk analizi ve çalışma alanlarını; Hammurabi ise mevzuat–içtihat bağlamı ve izlenebilir gerekçelendirmeyi öne çıkarmaktadır. Bu gözlemler LegalAI'nin ayrıştırıcı eksenini “zaman + merci + çözüm yolu + kanıt” birleşimi olarak belirler.

## Tasarım kaynakları

- [Argüman AI fiyatlandırma ve modül listesi](https://www.arguman.ai/pricing)
- [De Jure AI derin araştırma](https://www.dejure.ai/derin-arastirma) ve [dilekçe modülü](https://www.dejure.ai/dilekce)
- [Judis AI özellikleri](https://judis.ai/)
- [Apilex platformu](https://www.apilex.ai/)
- [Hammurabi araştırma ve doğrulama yaklaşımı](https://hammurabi.tr/)
- [AYM resmi norm kararları veri tabanı](https://normkararlarbilgibankasi.anayasa.gov.tr/ND/2026/13)
- [Danıştay resmi karar arama](https://karararama.danistay.gov.tr/)
- [Türkiye Barolar Birliği Avukatlık Kanunu m.35/A açıklaması](https://sertifikaliegitimler.barobirlik.org.tr/OtuzBesA/)
- [Adalet Bakanlığı Arabuluculuk Kanunu metni](https://adb.adalet.gov.tr/Resimler/SayfaDokuman/11120231556551.5.6325.pdf)
- [Adalet Bakanlığı İcra İşleri Dairesi arabuluculuk belgesi açıklaması](https://iidb.adalet.gov.tr/Resimler/SayfaDokuman/16092024094034Arabuluculuk%20Belgesinin%20%C4%B0cra%20Takibine%20Konu%20Edilmesi.pdf)

Defendiora için doğrulanabilir resmi ürün sayfası bulunamadığından, tasarım gereksinimi olarak bu ürünün doğrulanmamış kamuya açık iddiaları kullanılmamıştır.

## Kabul kriterleri

- Codex repo açıldığında `legalai` MCP sunucusunu proje config'inden görebilir ve araçları çağırabilir.
- Anahtarsız çağrıda süreç çökmez; host model için 5 karşı argüman ve zayıf nokta talimatı, gerçek arama sonuçları ve kaynaklandırma kuralı döner.
- API anahtarlı çağrıda OpenRouter veya DeepSeek model adı yalnızca env değiştirerek seçilebilir.
- `ENABLE_AGGRESSIVE_OPPOSING=false` güvenli biçimde aracı kapatır.
- Tüm yeni otomatik testler geçer ve mevcut testlerde regresyon oluşmaz.
- Ayrı hosting kurulumu yapılmaz; gelecekte remote MCP/HTTP için domain akışı ayrıştırılmış kalır.
