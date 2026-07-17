# Week 11 Keşif, Demo ve Health-Check Tasarım Belgesi

## Amaç

LegalAI'yi ilk kez kullanan, yazılım bilgisi olmayan bir kişinin dört farklı MCP istemcisinde aynı temel akışı anlayabilmesini sağlamak: bağlantıyı kontrol etmek, yetenekleri keşfetmek, yalın veya rafine kullanım seviyesini seçmek ve kaynaklı/ ihtimalli bir hukuki analiz istemek.

Bu sprint yeni bir hosting veya ortak sunucu kurmaz. Mevcut yerel STDIO MCP çalışma modelini korur.

## Kullanıcı deneyimi

Kullanıcı üç farklı giriş yoluna sahip olur:

1. **MCP istemcisi:** Kullanıcı önce `legalai_saglik_kontrolu`, sonra gerekirse `legalai_yardim` aracını seçer.
2. **Doğal dil:** Kullanıcı araç adlarını bilmeden doğrudan hukuki talebini yazar; host model MCP açıklamalarından uygun aracı seçer.
3. **Yerel CLI:** Kullanıcı `legalai qa "..."` komutuyla temel katmanlı analizi başlatabilir.

Yetenek seviyesi üç basamaklıdır:

- **Yalın:** Soru ve kısa bağlam.
- **Yönlendirilmiş:** Tarihler, taraf rolü, hukuk alanı ve istenen çıktı belirtilir.
- **Rafine:** Temporal context, süre riskleri, görev/yetki, karşıt içtihatlar, karşı taraf argümanları ve dava dışı çözüm yolları açıkça istenir.

## Mimari

```text
Kullanıcı
  ├─ IDE/CLI doğal dil ───────┐
  ├─ legalai_yardim            ├─ Host MCP istemcisi
  └─ legalai_saglik_kontrolu ─┘
              │
              ▼
       LegalAI yerel STDIO MCP
              │
              ├─ legalai_yardim / capabilities resource
              ├─ legalai_saglik_kontrolu (dış API yok)
              ├─ katmanli_analiz / agresif_karsi_taraf / derin_arastirma
              └─ yerel outbound PII maskesi
                         │
                         ▼
             Bedesten / AYM / HUDOC / seçilen LLM
```

`legalai_saglik_kontrolu` yalnızca süreç ve sürüm bilgisini döndürür. Ağ, veritabanı veya API anahtarı doğrulaması yapmaz; böylece yeni kurulumda güvenli ve deterministik bir bağlantı testi olarak kullanılabilir.

`legalai qa` aynı mevcut `run_pipeline(..., synthesize=False)` akışını kullanır. Yeni bir analiz motoru oluşturmaz; CLI ile MCP arasındaki davranışın ayrışmasını önler.

## Çıktı ve güvenlik sözleşmesi

- Hukuki sonuçlar `analysis_only=true` ve `non_binding=true` olarak kalır.
- Kaynaklar künye, belge kimliği ve mümkün olduğu ölçüde kısa alıntı ile gösterilir.
- Tarih veya olgu eksikse varsayımlar ve `missing_facts` görünür kalır.
- PII, LegalAI'nin başlattığı dış çağrılardan önce yerelde maskelenir.
- Demo metinleri gerçek kişi, dosya, TCKN, adres veya API anahtarı içermez.
- Kullanıcıya “kesin”, “garantili” veya bağlayıcı sonuç dili vaat edilmez.

## Dokümantasyon kapsamı

- README: beş dakikalık kurulum, desteklenen istemciler, Mermaid mimari şeması, dört ana modül ve katkı bağlantısı.
- `docs/week11-demo.md`: yeni kullanıcının kopyalayabileceği üç kullanım senaryosu, beklenen çıktı başlıkları, MCP menüsü ve CLI örneği.
- `CONTRIBUTING.md`: Python/uv kurulumu, test komutları, PII/secret kuralları, commit kapsamı ve PR kontrol listesi.

Gerçek demo videosu bu sprintte zorunlu artefakt değildir. Dokümantasyon, ekran videosu çekilmeden de takip edilebilir olmalıdır; kullanıcı isterse sonradan bu akıştan video kaydı alabilir.

## Hata davranışı

- Health-check her zaman yerel ve deterministik yanıt verir.
- `legalai qa` boş soru veya geçersiz seçenekleri kullanıcıya açık CLI hatasıyla bildirir.
- Uzak hukuk kaynağı erişilemezse mevcut pipeline'ın izlenebilir belirsizlik davranışı korunur; CLI hata mesajı traceback yerine anlaşılır bir açıklama verir.
- PII maskesi veya tenant bağlamı hatası dış çağrıya izin vermez; bu sınır mevcut güvenlik sözleşmesine göre korunur.

## Test kabul kriterleri

- Health-check MCP aracı tam olarak `status`, `version` ve `external_calls=false` alanlarını döndürür.
- `legalai qa` soru, mod ve jurisdiction seçeneklerini mevcut pipeline'a aktarır; JSON çıktıda non-binding alanları korunur.
- Boş soru ve geçersiz mod için CLI non-zero exit code verir.
- README, demo ve katkı belgelerinde gerçek secret veya kişisel veri bulunmaz.
- `.venv\Scripts\python.exe -m pytest -q` ve `uv run --no-cache pytest -q` yeşil olur.
- MCP metadata smoke testinde health-check, discovery tool ve capabilities resource görünür olur.

## Kapsam dışı

- Remote HTTP hosting veya ayrı server kurulumu.
- Gerçek video dosyası üretimi.
- Sözleşme inceleme, due diligence ve teknik bilirkişi itiraz modülünün üretim kodu.
- Host modelin ilk kullanıcı mesajını MCP'den önce maskelemesini garanti eden IDE proxy katmanı.
