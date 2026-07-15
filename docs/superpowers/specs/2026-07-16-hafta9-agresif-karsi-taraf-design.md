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

## Kabul kriterleri

- Codex repo açıldığında `legalai` MCP sunucusunu proje config'inden görebilir ve araçları çağırabilir.
- Anahtarsız çağrıda süreç çökmez; host model için 5 karşı argüman ve zayıf nokta talimatı, gerçek arama sonuçları ve kaynaklandırma kuralı döner.
- API anahtarlı çağrıda OpenRouter veya DeepSeek model adı yalnızca env değiştirerek seçilebilir.
- `ENABLE_AGGRESSIVE_OPPOSING=false` güvenli biçimde aracı kapatır.
- Tüm yeni otomatik testler geçer ve mevcut testlerde regresyon oluşmaz.
- Ayrı hosting kurulumu yapılmaz; gelecekte remote MCP/HTTP için domain akışı ayrıştırılmış kalır.
