# Hafta 14 Persona ve Kaynak Katmanı Uygulama Planı

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** LegalAI'nin olaydan birden fazla hukuk alanını algılayıp ilgili uzman personaları birlikte çalıştırmasını, dört aşamalı hukuki muhakemeyi ve doktrin/OECD kaynak politikalarını geriye dönük uyumlu biçimde uygulamak.

**Architecture:** Mevcut tekil `jurisdiction_id` alanı korunacak; buna ek olarak çoklu profil seçimi ve uzman lens kompozisyonu eklenecek. YAML profilleri persona metnini ve uzmanlık metadatasını taşırken, prompt kompozitörü tüm sunucu ve host-orchestrated akışlara aynı kuralları aktaracak. Kaynak katmanı ilk aşamada resmi/akademik kaynak sınıflandırmasını ve kullanım politikasını sağlayacak; canlı scraper geliştirmesi bu planın dışında ayrı bir plan olacaktır.

**Tech Stack:** Python 3.12+, `dataclasses`, YAML mevcut loader'ı, pytest, mevcut `Pipeline`/`Context`, FastMCP prompt üretim akışları.

## Global Constraints

- Mevcut `jurisdiction_id: str | None` alanı ve `guess_jurisdiction()` çağrısı geriye dönük çalışmaya devam edecek.
- Çıktılar `analysis_only` ve `non_binding` niteliğini koruyacak.
- Persona isimleri gerçek kişi/kurum kimliği iddiası değil, uzmanlık bakışıdır.
- Haksız rekabet hukuku ve rekabet hukuku ayrı sınıflandırılacak.
- OECD kaynakları bağlayıcı hukuk değil, rekabet araştırması ve gerektiğinde konu-kesişimli yardımcı kaynak olarak etiketlenecek.
- Kişisel ayar dosyaları `.cursor/mcp.json` ve `.superpowers/` commit edilmeyecek.
- Her kod adımı önce başarısız test, sonra asgari uygulama, sonra hedefli test ve commit döngüsüyle tamamlanacak.
- Kaynakların tam metin saklanması lisans/telif durumuna göre sınırlandırılacak; bu plan canlı scraping veya lisans bypass'ı içermez.

---

## Dosya Haritası

**Değiştirilecek dosyalar:**

- `legalai/packages/jurisdictions/base.py` — persona ve çoklu uzmanlık alanlarının profil şeması.
- `legalai/packages/layers/pipeline.py` — çoklu profil seçim sonuçlarını taşıyan `Context` alanları.
- `legalai/packages/layers/qualify_issue.py` — tekil tahmin korunarak çoklu alan skorlaması.
- `legalai/packages/layers/select_jurisdiction_profile.py` — profil listesi, `diger` fallback'i ve güven bilgisi.
- `legalai/packages/layers/analysis_pipeline.py` — dört muhakeme adımını ve çoklu persona talimatını host akışına aktarma.
- `legalai/packages/layers/grounded_generator.py` — server-side LLM system prompt kompozisyonu.
- `legalai/packages/layers/opposing.py` — agresif karşı taraf akışında persona ve muhakeme kuralları.
- `legalai/packages/layers/deep_research.py` — araştırma alt sorularında çoklu persona ve kaynak kapsamı.

**Oluşturulacak dosyalar:**

- `legalai/packages/jurisdictions/selection.py` — `JurisdictionSelection` ve seçim yardımcıları.
- `legalai/packages/jurisdictions/persona.py` — profil/persona prompt kompozitörü.
- `legalai/packages/sources/policy.py` — doktrin, kurum ve OECD kaynak kullanım politikası.
- `legalai/configs/sources/doctrine.yaml` — doktrin kaynak sınıfları ve telif/erişim kuralları.
- `legalai/configs/sources/competition.yaml` — Rekabet Kurumu, AB ve OECD kapsamları.
- `legalai/tests/jurisdictions/test_persona_selection.py` — çoklu alan ve fallback testleri.
- `legalai/tests/jurisdictions/test_persona_composer.py` — persona kompozisyonu testleri.
- `legalai/tests/sources/test_source_policy.py` — kaynak kullanım politikası testleri.
- `legalai/tests/layers/test_reasoning_instructions.py` — dört muhakeme adımı testleri.

**Güncellenecek YAML profilleri:**

- `legalai/configs/jurisdictions/hukuk.yaml`
- `legalai/configs/jurisdictions/ceza.yaml`
- `legalai/configs/jurisdictions/idare.yaml`
- `legalai/configs/jurisdictions/aym.yaml`
- `legalai/configs/jurisdictions/kik.yaml` oluşturulacaksa mevcut şablona göre eklenecek.
- `legalai/configs/jurisdictions/vergi.yaml`
- `legalai/configs/jurisdictions/rekabet.yaml`
- `legalai/configs/jurisdictions/kvkk.yaml`
- `legalai/configs/jurisdictions/diger.yaml`

---

### Task 1: Persona profil şemasını geriye dönük uyumlu hale getir

**Files:**
- Modify: `legalai/packages/jurisdictions/base.py:9-42`
- Modify: `legalai/tests/jurisdictions/test_loader.py`
- Create: `legalai/tests/jurisdictions/test_persona_profiles.py`

**Interfaces:**
- `JurisdictionProfile` yeni alanları üretir: `system_prompt_persona: str`, `response_tone: str`, `disclaimer_required: bool`, `expert_lenses: list[str]`, `analysis_focus: list[str]`.
- `JurisdictionProfile.from_dict(data)` eksik alanlarda boş liste/boş metin/`False` varsayılanlarını kullanır.

- [ ] **Step 1: YAML persona alanları için başarısız test yaz**

```python
def test_profile_reads_persona_and_lenses():
    profile = JurisdictionProfile.from_dict({
        "id": "hukuk",
        "name": "Hukuk",
        "system_prompt_persona": "Kıdemli hukukçu perspektifi.",
        "response_tone": "resmi",
        "disclaimer_required": True,
        "expert_lenses": ["ticaret", "haksiz_rekabet"],
        "analysis_focus": ["gorev_yetki", "sureler"],
    })
    assert profile.system_prompt_persona.startswith("Kıdemli")
    assert profile.expert_lenses == ["ticaret", "haksiz_rekabet"]
    assert profile.disclaimer_required is True
```

- [ ] **Step 2: Testi çalıştır ve yeni alan eksikliğini gözlemle**

Run: `uv run pytest legalai/tests/jurisdictions/test_persona_profiles.py -q`

Expected: FAIL because the dataclass does not expose the new fields.

- [ ] **Step 3: Dataclass alanlarını ve `from_dict` eşlemesini ekle**

```python
system_prompt_persona: str = ""
response_tone: str = ""
disclaimer_required: bool = False
expert_lenses: list[str] = field(default_factory=list)
analysis_focus: list[str] = field(default_factory=list)
```

`from_dict` içinde alanları `data.get(...)` ile oku; mevcut alanların sırasını ve `raw=data` davranışını değiştirme.

- [ ] **Step 4: Hedefli ve mevcut jurisdiction testlerini çalıştır**

Run: `uv run pytest legalai/tests/jurisdictions -q`

Expected: PASS; mevcut profiller persona alanı eklenmeden de yüklenmeye devam eder.

- [ ] **Step 5: Commit**

```bash
git add legalai/packages/jurisdictions/base.py legalai/tests/jurisdictions/test_loader.py legalai/tests/jurisdictions/test_persona_profiles.py
git commit -m "feat: extend jurisdiction profiles with persona metadata"
```

### Task 2: Çoklu profil seçimi ve uzmanlık kataloğunu ekle

**Files:**
- Create: `legalai/packages/jurisdictions/selection.py`
- Modify: `legalai/packages/layers/pipeline.py:12-31`
- Modify: `legalai/packages/layers/qualify_issue.py:1-45`
- Modify: `legalai/packages/layers/select_jurisdiction_profile.py:1-28`
- Test: `legalai/tests/jurisdictions/test_persona_selection.py`
- Modify: `legalai/tests/layers/test_qualify_issue.py`
- Modify: `legalai/tests/layers/test_select_jurisdiction_profile.py`

**Interfaces:**

```python
@dataclass
class JurisdictionSelection:
    primary: str
    supporting: list[str] = field(default_factory=list)
    expert_lenses: list[str] = field(default_factory=list)
    confidence: float = 0.0
    assumptions: list[str] = field(default_factory=list)

def guess_jurisdictions(question: str) -> JurisdictionSelection: ...
```

`guess_jurisdiction(question)` mevcut dış çağrılar için `(primary | None, scores)` döndüren uyumluluk wrapper'ı olarak kalır.

- [ ] **Step 1: Çoklu hukuk alanı ve bilinmeyen soru için başarısız test yaz**

```python
def test_guess_jurisdictions_detects_hukuk_and_ceza():
    selection = guess_jurisdictions("Sözleşme alacağı için sahte belge düzenlenmiş olabilir mi?")
    assert selection.primary in {"hukuk", "ceza"}
    assert {"hukuk", "ceza"}.issubset({selection.primary, *selection.supporting})

def test_unknown_question_uses_diger_without_losing_confidence_metadata():
    selection = guess_jurisdictions("Bu olayın hukuki çözümünü araştır.")
    assert selection.primary == "diger"
    assert 0.0 <= selection.confidence <= 1.0
```

- [ ] **Step 2: Testleri çalıştır ve seçim API'sinin yokluğunu doğrula**

Run: `uv run pytest legalai/tests/jurisdictions/test_persona_selection.py legalai/tests/layers/test_qualify_issue.py -q`

Expected: FAIL because `guess_jurisdictions` and the new context fields do not exist.

- [ ] **Step 3: Çoklu skorlamayı ve `Context` alanlarını ekle**

`Context` içine mevcut `jurisdiction_id` alanını koruyarak şu alanları ekle:

```python
jurisdiction_ids: list[str] = field(default_factory=list)
expert_lenses: list[str] = field(default_factory=list)
jurisdiction_confidence: float = 0.0
```

Skorlanan alanları eşik üstünde supporting listesine al; hiçbir alan eşik üstünde değilse `primary="diger"`, `assumptions` içine özel profil bulunamadığını ekle.

- [ ] **Step 4: Pipeline katmanının eski ve yeni davranışını doğrula**

Run: `uv run pytest legalai/tests/layers/test_select_jurisdiction_profile.py legalai/tests/jurisdictions/test_persona_selection.py -q`

Expected: PASS; açık `jurisdiction_hint` tekil primary olarak korunur, otomatik bilinmeyen soru `diger` olur.

- [ ] **Step 5: Commit**

```bash
git add legalai/packages/jurisdictions/selection.py legalai/packages/layers/pipeline.py legalai/packages/layers/qualify_issue.py legalai/packages/layers/select_jurisdiction_profile.py legalai/tests/jurisdictions/test_persona_selection.py legalai/tests/layers/test_qualify_issue.py legalai/tests/layers/test_select_jurisdiction_profile.py
git commit -m "feat: support multi-jurisdiction persona selection"
```

### Task 3: Persona kompozitörü ve profilleri tanımla

**Files:**
- Create: `legalai/packages/jurisdictions/persona.py`
- Modify: `legalai/configs/jurisdictions/hukuk.yaml`
- Modify: `legalai/configs/jurisdictions/ceza.yaml`
- Modify: `legalai/configs/jurisdictions/idare.yaml`
- Modify: `legalai/configs/jurisdictions/aym.yaml`
- Create: `legalai/configs/jurisdictions/vergi.yaml`
- Create: `legalai/configs/jurisdictions/rekabet.yaml`
- Create: `legalai/configs/jurisdictions/kvkk.yaml`
- Create: `legalai/configs/jurisdictions/kik.yaml`
- Create: `legalai/configs/jurisdictions/diger.yaml`
- Test: `legalai/tests/jurisdictions/test_persona_composer.py`

**Interfaces:**

```python
def compose_persona_instructions(
    profile_ids: Sequence[str],
    expert_lenses: Sequence[str] = (),
) -> str: ...
```

The composer loads profiles through the existing loader, preserves the requested order, removes duplicate profile IDs, and emits explicit primary/supporting labels. It must never invent a profile that is not loaded.

- [ ] **Step 1: Composer output contract için başarısız test yaz**

```python
def test_composer_names_primary_and_supporting_profiles():
    text = compose_persona_instructions(["hukuk", "ceza"], ["sözleşmeler"])
    assert "PRIMARY_PROFILE: hukuk" in text
    assert "SUPPORTING_PROFILE: ceza" in text
    assert "sözleşmeler" in text
    assert "non-binding" in text
```

- [ ] **Step 2: Testi çalıştır ve kompozitör eksikliğini doğrula**

Run: `uv run pytest legalai/tests/jurisdictions/test_persona_composer.py -q`

Expected: FAIL because the module does not exist.

- [ ] **Step 3: YAML profillerini persona ve lens metadatasıyla doldur**

`hukuk.yaml` içinde en az şu lens anahtarları bulunmalı: `ticaret`, `is`, `tazminat`, `kisiler`, `esya`, `sozlesmeler`, `miras`, `fikri_sinai`, `haksiz_rekabet`, `marka`, `patent`, `deniz_ticareti`, `kira`, `bilisim`, `tuketici`, `saglik`, `sigorta`, `spor`, `enerji`, `insaat`.

Her yeni profil `system_prompt_persona`, `response_tone`, `disclaimer_required`, `expert_lenses` ve `analysis_focus` alanlarını içerir. Persona metinleri kişilik taklidi değil, uzman bakış ve kaynak disiplini talimatıdır.

- [ ] **Step 4: Kompozitörü minimal kaynaklı ve bağlayıcılık etiketli biçimde uygula**

Kompozitör; ortak non-binding kuralları, primary persona metnini, supporting persona metinlerini, seçilen alt lensleri ve belirsizlik kurallarını tek prompt bölümünde birleştirir. Aynı profile ikinci kez rastlanırsa tek kez yazılır.

- [ ] **Step 5: Tüm profillerin yüklenmesini ve kompozisyonu test et**

Run: `uv run pytest legalai/tests/jurisdictions -q`

Expected: PASS; tüm profillerin persona metni boş değildir, bilinmeyen profil loader hatası yerine `diger` seçiminden geçer.

- [ ] **Step 6: Commit**

```bash
git add legalai/packages/jurisdictions/persona.py legalai/configs/jurisdictions legalai/tests/jurisdictions/test_persona_composer.py
git commit -m "feat: add multi-domain legal persona profiles"
```

### Task 4: Kaynak politikası ve OECD/doktrin kapsamını ekle

**Files:**
- Create: `legalai/packages/sources/policy.py`
- Create: `legalai/configs/sources/doctrine.yaml`
- Create: `legalai/configs/sources/competition.yaml`
- Create: `legalai/tests/sources/test_source_policy.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class SourcePolicy:
    source_id: str
    label: str
    source_kind: str
    authority_level: str
    allowed_contexts: tuple[str, ...]
    full_text_storage: str
    citation_required: bool = True

def load_source_policies() -> dict[str, SourcePolicy]: ...
def policies_for_context(context: str) -> list[SourcePolicy]: ...
```

- [ ] **Step 1: Doktrin ve OECD kullanım sınırları için başarısız test yaz**

```python
def test_oecd_is_competition_research_only_by_default():
    policies = policies_for_context("competition_research")
    oecd = next(item for item in policies if item.source_id == "oecd_competition")
    assert oecd.authority_level == "non_binding_policy_reference"

def test_public_doctrine_requires_citation_and_license_metadata():
    policies = load_source_policies()
    doctrine = policies["dergipark_and_open_doctrine"]
    assert doctrine.citation_required is True
    assert doctrine.full_text_storage in {"allowed", "metadata_or_excerpt_only"}
```

- [ ] **Step 2: Testi çalıştır ve policy modülünün yokluğunu doğrula**

Run: `uv run pytest legalai/tests/sources/test_source_policy.py -q`

Expected: FAIL because source policy types and YAML files do not exist.

- [ ] **Step 3: Kaynak YAML sınıflarını ekle**

`doctrine.yaml` kaynakları DergiPark, baro/TBB dergileri, kamuya açık YÖK hukuk tezleri, Rekabet Kurumu uzmanlık tezleri ve Rekabet Dergisi olarak sınıflandırır. `competition.yaml` Rekabet Kurumu, AB Komisyonu, ABAD/Genel Mahkeme, EUR-Lex ve OECD kaynaklarını ayrı authority/kind değerleriyle tanımlar.

- [ ] **Step 4: Policy loader ve context filtrelemesini uygula**

OECD yalnızca `competition_research` ve açıkça konu-kesişimi verilen bağlamlarda döner. Her policy `citation_required=True` ile gelir; tam metin saklama `allowed` veya `metadata_or_excerpt_only` olarak açıkça belirtilir.

- [ ] **Step 5: Kaynak politika testlerini çalıştır**

Run: `uv run pytest legalai/tests/sources/test_source_policy.py -q`

Expected: PASS; OECD genel hukuk bağlamında varsayılan kaynak olarak dönmez, rekabet araştırmasında non-binding olarak döner.

- [ ] **Step 6: Commit**

```bash
git add legalai/packages/sources legalai/configs/sources legalai/tests/sources
git commit -m "feat: add doctrine and competition source policies"
```

### Task 5: Dört aşamalı hukuki muhakeme talimatlarını üret

**Files:**
- Create: `legalai/packages/layers/legal_reasoning.py`
- Create: `legalai/tests/layers/test_reasoning_instructions.py`
- Modify: `legalai/packages/layers/analysis_pipeline.py:120-137`

**Interfaces:**

```python
REASONING_STEPS: tuple[str, str, str, str]

def build_reasoning_instructions(
    jurisdiction_ids: Sequence[str] = (),
    source_context: str = "legal_analysis",
) -> str: ...
```

- [ ] **Step 1: Dört adımın sıra ve içeriği için başarısız test yaz**

```python
def test_reasoning_instructions_contain_four_ordered_steps():
    text = build_reasoning_instructions(["hukuk", "ceza"])
    positions = [text.index(marker) for marker in (
        "1. Hukuki sorun nedir?",
        "2. Teorik ve yasal altyapı nedir?",
        "3. Somut olayın unsurlarla ilişkisi nedir?",
        "4. Cevap ve strateji nedir?",
    )]
    assert positions == sorted(positions)
    assert "Temporal Legal Context" in text
    assert "karşıt görüş" in text
```

- [ ] **Step 2: Testi çalıştır ve helper eksikliğini doğrula**

Run: `uv run pytest legalai/tests/layers/test_reasoning_instructions.py -q`

Expected: FAIL because the helper does not exist.

- [ ] **Step 3: Helper'ı ve kaynaklı strateji kurallarını uygula**

Helper; dört adımı, tarih/süre/görev-yetki denetimini, karşıt görüş taramasını, doktrin/kurum/OECD authority etiketlerini ve `analysis_only`/`non_binding` uyarısını üretir.

- [ ] **Step 4: Host-orchestrated analiz talimatına helper'ı bağla**

`build_assistant_instructions(valid_doc_ids, jurisdiction_ids=())` imzasını geriye uyumlu biçimde genişlet; mevcut çağrılar boş default ile çalışsın. `analysis_pipeline.py` seçim sonucu ve source context'i helper'a aktarır.

- [ ] **Step 5: Analiz talimatı testlerini çalıştır**

Run: `uv run pytest legalai/tests/layers/test_reasoning_instructions.py legalai/tests/layers/test_analysis_pipeline.py -q`

Expected: PASS; eski belge listesi ve yeni dört-adım muhakeme metni birlikte üretilir.

- [ ] **Step 6: Commit**

```bash
git add legalai/packages/layers/legal_reasoning.py legalai/packages/layers/analysis_pipeline.py legalai/tests/layers/test_reasoning_instructions.py
git commit -m "feat: add structured legal reasoning instructions"
```

### Task 6: Tüm LLM ve strateji yüzeylerine persona kompozisyonunu aktar

**Files:**
- Modify: `legalai/packages/layers/grounded_generator.py:29-65`
- Modify: `legalai/packages/layers/opposing.py:227-317`
- Modify: `legalai/packages/layers/deep_research.py:128-176`
- Test: `legalai/tests/layers/test_grounded_generator.py`
- Test: `legalai/tests/layers/test_opposing.py`
- Test: `legalai/tests/layers/test_deep_research.py`

**Interfaces:**

```python
def build_system_prompt(
    jurisdiction_id: str | None = None,
    jurisdiction_ids: Sequence[str] = (),
    expert_lenses: Sequence[str] = (),
) -> str: ...
```

Eski tek parametreli çağrı `build_system_prompt("hukuk")` aynı sonucu üretmeye devam eder.

- [ ] **Step 1: Her yüzey için persona aktarımını kanıtlayan başarısız testleri yaz**

Testler, mocked LLM/system instruction içinde `hukuk`, `ceza`, `Temporal Legal Context`, dört muhakeme adımı ve non-binding uyarısını arar. Host-orchestrated opposing/deep research çıktılarında da aynı talimatların bulunduğunu doğrular.

- [ ] **Step 2: Hedefli testleri çalıştır ve mevcut persona eksikliğini doğrula**

Run: `uv run pytest legalai/tests/layers/test_grounded_generator.py legalai/tests/layers/test_opposing.py legalai/tests/layers/test_deep_research.py -q`

Expected: Yeni çoklu-persona assertions FAIL; mevcut davranış regressions vermeden çalışır.

- [ ] **Step 3: GroundedGenerator ve host akışlarını kompozitöre bağla**

Context'teki `jurisdiction_ids`, `expert_lenses` ve primary `jurisdiction_id` alanlarını persona kompozitörüne geçir. Opposing ve deep research'te mevcut profile axes/subquestion mantığını koruyarak persona talimatını ortak helper üzerinden ekle.

- [ ] **Step 4: Hedefli testleri çalıştır**

Run: `uv run pytest legalai/tests/layers/test_grounded_generator.py legalai/tests/layers/test_opposing.py legalai/tests/layers/test_deep_research.py -q`

Expected: PASS; server-side ve host-orchestrated akışlar aynı persona/muhakeme kurallarını taşır.

- [ ] **Step 5: Commit**

```bash
git add legalai/packages/layers/grounded_generator.py legalai/packages/layers/opposing.py legalai/packages/layers/deep_research.py legalai/tests/layers/test_grounded_generator.py legalai/tests/layers/test_opposing.py legalai/tests/layers/test_deep_research.py
git commit -m "feat: propagate multi-domain personas across analysis surfaces"
```

### Task 7: Kabul testleri, MCP smoke ve tam doğrulama

**Files:**
- Modify: `legalai/tests/jurisdictions/test_acceptance_hafta3.py`
- Create: `legalai/tests/jurisdictions/test_acceptance_hafta14.py`
- Modify: `docs/mcp-client-matrix.md` — kullanıcıya görünen persona/kaynak davranışı.

- [ ] **Step 1: Hafta 14 kabul testlerini yaz**

Testler şu sözleşmeleri kapsar:

```python
assert "haksiz_rekabet" != "rekabet"
assert unknown_selection.primary == "diger"
assert set(multi.supporting) >= {"ceza"}
assert "4. Cevap ve strateji nedir?" in reasoning
assert oecd.authority_level == "non_binding_policy_reference"
```

- [ ] **Step 2: Hedefli kabul testlerini çalıştır**

Run: `uv run pytest legalai/tests/jurisdictions legalai/tests/sources legalai/tests/layers/test_reasoning_instructions.py -q`

Expected: PASS.

- [ ] **Step 3: Mevcut tam test paketini çalıştır**

Run: `uv run pytest -q`

Expected: PASS; eski testlerde kırılma olmamalı.

- [ ] **Step 4: MCP health/discovery/resources smoke testini çalıştır**

Run: `uv run pytest legalai/tests/apps/test_mcp_client_matrix.py -q`

Expected: PASS; `legalai_saglik_kontrolu`, capability discovery ve mevcut istemci kayıtları korunur.

- [ ] **Step 5: Kullanıcı dokümantasyonunu güncelle**

`docs/mcp-client-matrix.md` içine şu doğal dil örneklerini ekle:

```text
Bu olayı hukuk ve ceza personalarıyla birlikte analiz et.
Haksız rekabet ile rekabet hukuku ihtimallerini birbirinden ayır.
OECD kaynaklarını yalnızca rekabet politikası ve ekonomik analiz için kullan.
```

- [ ] **Step 6: Son doğrulama ve checkpoint commit**

```bash
git add legalai/tests/jurisdictions/test_acceptance_hafta14.py docs/mcp-client-matrix.md
git commit -m "test: verify week 14 persona and source behavior"
```

## Uygulama dışı kalanlar

Bu plan, kaynakların canlı olarak scrape edilmesini, lisanslı veri sağlayıcı entegrasyonunu, yeni bir uzak hosting servisini, sözleşme inceleme/due diligence uygulamasını ve teknik bilirkişi raporu itiraz motorunu uygulamaz. Bu özellikler, bu planın ürettiği persona/source policy arayüzlerini kullanacak ayrı uygulama planlarıdır.

## Handoff

Plan onaylandıktan sonra `superpowers:subagent-driven-development` ile her görev ayrı bir alt görev olarak uygulanır; her görevden sonra test, diff incelemesi ve küçük commit yapılır. Windows ortamında subagent başlatma tekrar takılırsa aynı görev sırası korunarak inline TDD uygulanır ve durum kullanıcıya bildirilir.

