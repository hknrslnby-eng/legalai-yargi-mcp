# Ticaret Savunması Persona ve Kaynak Politikası Tasarımı

## Amaç

LegalAI'ye damping, sübvansiyon/telafi edici vergi ve korunma tedbirleri sorularını mevcut çoklu hukuk alanı, persona, dört aşamalı muhakeme ve kaynak politikası omurgasıyla ele alan `ticaret_savunmasi` profili eklenecek. Türkiye mevzuatı ve Ticaret Bakanlığı uygulaması birincil kabul edilecek; DTÖ, AB ve ABD içerikleri yalnızca karşılaştırmalı referans olarak etiketlenecek.

## Kapsam

- `ticaret_savunmasi` jurisdiction profilinin YAML şeması ve persona metni.
- Damping marjı, sübvansiyon, zarar/nedensellik, korunma tedbiri, usul/süre ve GTİP/benzer mal eksenleri.
- Gümrük, vergi, ürün/GTİP, ticaret politikası savunması, DTÖ, AB ve ABD trade-remedy lensleri.
- Damping, sübvansiyon, telafi edici vergi, korunma tedbiri, GTİP, menşe ve soruşturma ifadeleriyle otomatik seçim.
- Türkiye, DTÖ, AB, ABD ve doktrin kaynaklarının authority-level politikası.
- `katmanli_analiz`, `agresif_karsi_taraf` ve `derin_arastirma` çağrılarında `trade_defense_research` context yönlendirmesi.
- Uçtan uca persona/reasoning kabul testleri ve kullanıcıya görünürlük dokümantasyonu.

## Mimari

Kullanıcı sorusu `guess_jurisdictions()` üzerinden puanlanır. Ticaret savunması anahtarları bulunduğunda `ticaret_savunmasi` primary profile seçilir; destekleyici alanlar ve uzman lensleri mevcut çoklu seçim davranışıyla korunur. Profil `load_profile()` tarafından YAML'dan yüklenir ve ortak persona kompozitörü ile dört aşamalı muhakeme üreticisine aktarılır.

Kaynak context seçimi mevcut öncelik mantığına eklenecek:

```python
source_context = (
    "trade_defense_research" if "ticaret_savunmasi" in jurisdiction_ids
    else "competition_research" if "rekabet" in jurisdiction_ids
    else "legal_analysis"
)
```

Bu değişiklik LLM çağrılarını, araç sözleşmelerini ve mevcut çıktı modelini değiştirmez; yalnızca seçilen alanın kaynak politikasını doğru context'e taşır.

## Persona ve hukuk disiplini

Persona rolleri gerçek kişi veya kurum kimliği iddiası değil, uzmanlık lensidir. Persona metni:

1. Türkiye hukukunu birincil ve bağlayıcı çerçeve olarak sunar.
2. Ticaret Bakanlığı İthalat Genel Müdürlüğü, ilgili değerlendirme kurulları ve Danıştay yollarını Türkiye bağlamında işler.
3. DTÖ Anti-Damping, SCM ve Safeguards anlaşmalarını; AB düzenlemelerini ve ABD Title VII yapısını karşılaştırmalı referans olarak gösterir.
4. Yerli üretici/şikâyetçi için hücum ve ihracatçı/ithalatçı için savunma stratejilerini ayrı senaryolar halinde üretir.
5. GTİP/HS, menşe, benzer mal, fiyat karşılaştırması, maliyet güvenilirliği, zarar ve nedensellik ilişkisini teknik-hukuki birlikte değerlendirir.
6. Kesin süre veya mevzuat ayrıntısı doğrulanmamışsa `[DOĞRULAYIN]` işareti ve açık belirsizlik notu kullanır.

Tüm sonuçlar `analysis_only=True` ve `non_binding=True` niteliğini korur. EvidenceBlock alanları ve Temporal Legal Context kuralları mevcut katmanlardan aynen devralınır.

## Kaynak politikası

`trade_defense.yaml` aşağıdaki kaynak sınırlarını tanımlar:

| Kaynak | Authority level | Kullanım |
| --- | --- | --- |
| Ticaret Bakanlığı İthalat Genel Müdürlüğü | `domestic_institution_decision` | Türkiye hukuk analizi ve ticaret savunması araştırması |
| DTÖ anlaşmaları ve DSB kararları | `comparative_legislation` | Karşılaştırmalı ticaret savunması referansı |
| AB ticaret savunması düzenlemeleri ve DG TRADE | `comparative_institution_reference` | Karşılaştırmalı kurum/mevzuat referansı |
| ABAD/Genel Mahkeme kararları | `comparative_judicial_reference` | Karşılaştırmalı yargısal referans |
| USDOC/USITC tespitleri | `comparative_institution_reference` | Karşılaştırmalı kurum referansı |
| Ticaret politikası savunması doktrini | `non_binding_doctrine` | Doktrin araştırması |

Yabancı ve doktrin kaynakları metadata veya izin verilen kısa alıntı düzeyinde saklanır; Türk hukukunun yerine geçirilmez.

## Hata yönetimi ve sınırlar

- Profil YAML'ı eksikse mevcut `JurisdictionNotFoundError` davranışı korunur.
- Tanınmayan soru, mevcut `diger` fallback'ine düşer.
- Keyword çakışmalarında mevcut puanlama ve destekleyici jurisdiction davranışı korunur.
- Kaynak context bilinmiyorsa `legal_analysis` fallback'i korunur.
- Kesin sayısal süreler ve doğrulanmamış kanun/madde bilgileri kesin hüküm gibi üretilmez.
- Bu iş canlı mevzuat scrape'i, uzak veri sağlayıcı entegrasyonu veya yeni LLM sağlayıcısı eklemez.

## Test yaklaşımı

TDD sırası korunur: önce her davranış için başarısız test, sonra minimum uygulama, ardından hedefli ve regresyon testleri. Kabul ölçütleri:

- Profil beklenen alanları ve disclaimer'ı taşır.
- Ticaret savunması sorusu primary profile ve uygun lenslere yönlenir.
- Her kaynak authority level ve allowed context ile yüklenir.
- Üç ilgili reasoning yüzeyi `trade_defense_research` context'ini seçer.
- Persona ve reasoning uçtan uca aynı selection sonucunu taşır.
- Özellik alanı testleri geçer; mevcut repo genelindeki önceden var olan test collection çakışmaları ayrıca raporlanır.

## Geri alınabilirlik ve adlandırma

Uygulama `feature/anti-damping-savunmasi` dalında ve `.worktrees/anti-damping-savunmasi` worktree'sinde yapılır. Yeni Git ref, worktree ve dosya adlarında yalnızca ASCII karakter kullanılır. Mevcut Unicode dalına rename, force-push, rebase veya mevcut kirli çalışma ağacını değiştirme yapılmaz.
