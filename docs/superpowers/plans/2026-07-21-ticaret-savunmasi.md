# Ticaret Savunması Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Turkish-primary trade-defense persona, routing, source policy, and reasoning-context integration for anti-dumping, subsidy, and safeguard questions.

**Architecture:** Add one YAML jurisdiction profile and one YAML source-policy group, then connect them to the existing deterministic keyword selection and shared persona/reasoning builders. Keep all existing MCP tools and LLM call contracts unchanged; only derive `trade_defense_research` when the new jurisdiction is selected.

**Tech Stack:** Python 3.12, YAML, pytest, existing LegalAI jurisdiction/source/layer modules, uv-backed project environment.

## Global Constraints

- All outputs remain `analysis_only=True` and `non_binding=True`.
- Evidence metadata follows the existing `EvidenceBlock` fields and citation rules.
- Turkish law is primary and binding; WTO/EU/US material is comparative reference only.
- Unverified legal numbers, dates, article references, and deadlines carry `[DOĞRULAYIN]`.
- Persona roles are expertise lenses, not real identity claims.
- New Git refs, worktrees, and file names use ASCII only: `feature/anti-damping-savunmasi`.
- Do not modify the existing dirty checkout or rename/force-push the Unicode branch.

---

### Task 1: Add and validate the trade-defense jurisdiction profile

**Files:**
- Create: `legalai/configs/jurisdictions/ticaret_savunmasi.yaml`
- Test: `legalai/tests/jurisdictions/test_ticaret_savunmasi_profile.py`

**Interfaces:**
- Consumes: `load_profile(jid: str) -> JurisdictionProfile`.
- Produces: profile id `ticaret_savunmasi`, axes, expert lenses, procedural metadata, persona text, tone, and disclaimer flag.

- [ ] **Step 1: Write the failing profile-shape test**

```python
from legalai.packages.jurisdictions.loader import load_profile


def test_ticaret_savunmasi_profile_loads_with_expected_shape():
    profile = load_profile("ticaret_savunmasi")

    assert profile.id == "ticaret_savunmasi"
    assert len(profile.axes) >= 4
    assert "damping_marji" in profile.axes
    assert "gumruk_hukuku" in profile.expert_lenses
    assert profile.disclaimer_required is True
    assert profile.system_prompt_persona.startswith("Kıdemli")
```

- [ ] **Step 2: Run the test and verify the expected missing-profile failure**

Run: `& 'C:\Users\hakan\Desktop\Yargi MCP Fork\legalai-yargi-mcp\.venv\Scripts\python.exe' -m pytest legalai/tests/jurisdictions/test_ticaret_savunmasi_profile.py -q`

Expected: FAIL with `JurisdictionNotFoundError` because the YAML does not exist.

- [ ] **Step 3: Add the minimum complete YAML profile**

```yaml
id: ticaret_savunmasi
name: Ticaret Politikası Savunma Araçları (Damping, Sübvansiyon, Korunma Tedbirleri)
version: 1
axes: [damping_marji, subvansiyon_tespiti, zarar_ve_nedensellik, korunma_tedbiri_sartlari, usul_ve_sureler, gtip_ve_benzer_mal]
hierarchy: [TICARET_BAKANLIGI, TICARET_BAKANLIGI_TEBLIGI, DANISTAY, DTO_UYUSMAZLIK_COZUMU]
expert_lenses: [gumruk_hukuku, dis_ticaret, vergi_hukuku, urun_gtip, dto_hukuku, ab_ticaret_hukuku, abd_trade_remedy]
analysis_focus: [sorusturma_takvimi, damping_marji_hesap, zarar_analizi, karsit_arguman, strateji, gtip_tespiti]
procedural_deadlines:
  application_to_initiation: "Başvuru, ön inceleme ve açılış koşulları [DOĞRULAYIN]."
  provisional_measure: "Geçici önlem koşulları ve süresi [DOĞRULAYIN]."
  definitive_measure: "Kesin önlem koşulları ve yürürlük süresi [DOĞRULAYIN]."
  review: "Nihai ve ara gözden geçirme süreleri [DOĞRULAYIN]."
system_prompt_persona: |
  Kıdemli gümrük, vergi ve ürün/GTİP uzmanı lenslerini; Ticaret Bakanlığı İthalat Genel Müdürlüğü, ilgili değerlendirme kurulları ve ticaret politikası savunması avukatlığı ile birlikte kullan.
  Türk mevzuatını birincil ve bağlayıcı kabul et. DTÖ anlaşmaları, AB ticaret savunması düzenlemeleri ve ABD Title VII uygulamasını karşılaştırmalı, non-binding referans olarak etiketle.
  Damping, sübvansiyon/telafi edici vergi ve korunma tedbirlerinde ürün kapsamı, GTİP, menşe, benzer mal, fiyat/maliyet karşılaştırması, zarar ve nedensellik unsurlarını ayrı ayrı test et.
  Yerli üretici/şikâyetçi ile ihracatçı/ithalatçı için hücum ve savunma senaryolarını; usul, delil, süre ve itiraz yollarını açıkça ayır.
  Kesin sayısal süre veya mevzuat bilgisi doğrulanmadığında [DOĞRULAYIN] işareti kullan; çıktıyı analysis-only ve non-binding tut.
response_tone: resmi, temkinli, atıf-odaklı
disclaimer_required: true
```

- [ ] **Step 4: Run the focused test and verify it passes**

Run: `& 'C:\Users\hakan\Desktop\Yargi MCP Fork\legalai-yargi-mcp\.venv\Scripts\python.exe' -m pytest legalai/tests/jurisdictions/test_ticaret_savunmasi_profile.py -q`

Expected: PASS.

- [ ] **Step 5: Commit the profile**

```powershell
git add legalai/configs/jurisdictions/ticaret_savunmasi.yaml legalai/tests/jurisdictions/test_ticaret_savunmasi_profile.py
git commit -m "feat: add trade defense jurisdiction profile"
```

### Task 2: Route trade-defense questions and expert lenses

**Files:**
- Modify: `legalai/packages/jurisdictions/keywords.py`
- Modify: `legalai/packages/jurisdictions/selection.py`
- Modify: `legalai/tests/jurisdictions/test_persona_selection.py`

**Interfaces:**
- Consumes: `JURISDICTION_KEYWORDS`, `_LENS_KEYWORDS`, and `guess_jurisdictions(question)`.
- Produces: `selection.primary == "ticaret_savunmasi"` for trade-defense questions and relevant lens ids.

- [ ] **Step 1: Add a failing routing test**

```python
def test_trade_defense_question_selects_ticaret_savunmasi():
    selection = guess_jurisdictions(
        "Çin menşeli çelik ürünlere karşı dampinge karşı vergi soruşturması açıldı, GTİP itirazı ve savunma stratejisi ne olmalı?"
    )

    assert selection.primary == "ticaret_savunmasi"
    assert "gumruk_hukuku" in selection.expert_lenses
```

- [ ] **Step 2: Run the test and verify it fails with the old fallback/selection**

Run: `& 'C:\Users\hakan\Desktop\Yargi MCP Fork\legalai-yargi-mcp\.venv\Scripts\python.exe' -m pytest legalai/tests/jurisdictions/test_persona_selection.py::test_trade_defense_question_selects_ticaret_savunmasi -q`

Expected: FAIL because no trade-defense keyword group or gümrük lens exists.

- [ ] **Step 3: Add ASCII-safe ids with Turkish keyword content**

Add this entry to `JURISDICTION_KEYWORDS`:

```python
    "ticaret_savunmasi": [
        "damping", "dampinge karşı", "anti-dumping", "sübvansiyon",
        "telafi edici vergi", "korunma tedbiri", "ithalatta haksız rekabet",
        "gtip", "ithalat soruşturması", "gözden geçirme soruşturması",
    ],
```

Add these entries to `_LENS_KEYWORDS`:

```python
    "gumruk_hukuku": ("gümrük", "gtip", "menşe", "gümrük vergisi"),
    "urun_gtip": ("gtip", "hs code", "benzer mal", "ürün", "menşe"),
```

- [ ] **Step 4: Run routing and regression tests**

Run: `& 'C:\Users\hakan\Desktop\Yargi MCP Fork\legalai-yargi-mcp\.venv\Scripts\python.exe' -m pytest legalai/tests/jurisdictions/test_persona_selection.py legalai/tests/jurisdictions/test_ticaret_savunmasi_profile.py -q`

Expected: PASS with existing selection tests unchanged.

- [ ] **Step 5: Commit routing changes**

```powershell
git add legalai/packages/jurisdictions/keywords.py legalai/packages/jurisdictions/selection.py legalai/tests/jurisdictions/test_persona_selection.py
git commit -m "feat: route trade defense questions"
```

### Task 3: Add the trade-defense source policy

**Files:**
- Create: `legalai/configs/sources/trade_defense.yaml`
- Modify: `legalai/tests/sources/test_source_policy.py`

**Interfaces:**
- Consumes: `load_source_policies()` and `policies_for_context(context)`.
- Produces: six source policies for domestic, WTO, EU, US, and doctrine references.

- [ ] **Step 1: Add a failing authority-level test**

```python
def test_trade_defense_sources_load_with_expected_authority_levels():
    policies = load_source_policies()

    assert policies["ticaret_bakanligi_ithalat"].authority_level == "domestic_institution_decision"
    assert policies["wto_trade_remedy_agreements"].authority_level == "comparative_legislation"
    assert "trade_defense_research" in policies["eu_trade_defense_regulations"].allowed_contexts
```

- [ ] **Step 2: Run the test and verify the missing-key failure**

Run: `& 'C:\Users\hakan\Desktop\Yargi MCP Fork\legalai-yargi-mcp\.venv\Scripts\python.exe' -m pytest legalai/tests/sources/test_source_policy.py::test_trade_defense_sources_load_with_expected_authority_levels -q`

Expected: FAIL with `KeyError` because the source policy file does not exist.

- [ ] **Step 3: Create the six source entries**

Use `source_kind`, `authority_level`, `allowed_contexts`, and `full_text_storage` exactly as specified in `2026-07-21-ticaret-savunmasi-design.md`; domestic Ministry sources allow full text, comparative and doctrine sources use `metadata_or_excerpt_only`.

- [ ] **Step 4: Run source-policy tests**

Run: `& 'C:\Users\hakan\Desktop\Yargi MCP Fork\legalai-yargi-mcp\.venv\Scripts\python.exe' -m pytest legalai/tests/sources/test_source_policy.py -q`

Expected: PASS.

- [ ] **Step 5: Commit source policy**

```powershell
git add legalai/configs/sources/trade_defense.yaml legalai/tests/sources/test_source_policy.py
git commit -m "feat: add trade defense source policy"
```

### Task 4: Select trade-defense research context in all reasoning surfaces

**Files:**
- Modify: `legalai/packages/layers/analysis_pipeline.py`
- Modify: `legalai/packages/layers/deep_research.py`
- Modify: `legalai/tests/layers/test_analysis_pipeline.py`
- Modify: `legalai/tests/layers/test_deep_research.py`
- Modify: `legalai/tests/jurisdictions/test_acceptance_hafta14.py`

**Interfaces:**
- Consumes: jurisdiction id sequences at the existing three call sites.
- Produces: `trade_defense_research` for `ticaret_savunmasi`, then `competition_research` for `rekabet`, otherwise `legal_analysis`.

- [ ] **Step 1: Add a failing integration assertion for the pipeline prompt**

```python
def test_pipeline_uses_trade_defense_source_context_for_trade_defense_profile():
    prompt = build_assistant_instructions(
        [], jurisdiction_ids=["ticaret_savunmasi"]
    )

    assert "Kaynak bağlamı: trade_defense_research" in prompt
```

- [ ] **Step 2: Run the new test and verify it sees the old legal-analysis context**

Run: `& 'C:\Users\hakan\Desktop\Yargi MCP Fork\legalai-yargi-mcp\.venv\Scripts\python.exe' -m pytest legalai/tests/layers/test_analysis_pipeline.py::test_pipeline_uses_trade_defense_source_context_for_trade_defense_profile -q`

Expected: FAIL because the current pipeline only recognizes `rekabet`.

- [ ] **Step 3: Replace the pipeline context expression**

At the existing `analysis_pipeline.py` selection point, use:

```python
source_context = (
    "trade_defense_research" if "ticaret_savunmasi" in jurisdiction_ids
    else "competition_research" if "rekabet" in jurisdiction_ids
    else "legal_analysis"
)
```

Use the same precedence expression at both `deep_research.py` reasoning call sites.

- [ ] **Step 4: Add and run direct reasoning/source tests**

```python
def test_trade_defense_reasoning_uses_trade_defense_sources():
    reasoning = build_reasoning_instructions(
        ["ticaret_savunmasi"], source_context="trade_defense_research"
    )
    policies = load_source_policies()

    assert "4. Cevap ve strateji nedir?" in reasoning
    assert "trade_defense_research" in reasoning
    assert policies["wto_trade_remedy_agreements"].authority_level == "comparative_legislation"
```

Run: `& 'C:\Users\hakan\Desktop\Yargi MCP Fork\legalai-yargi-mcp\.venv\Scripts\python.exe' -m pytest legalai/tests/layers/test_analysis_pipeline.py legalai/tests/layers/test_deep_research.py legalai/tests/layers/test_reasoning_instructions.py legalai/tests/jurisdictions/test_acceptance_hafta14.py -q`

Expected: PASS, with existing competition and legal-analysis contexts unchanged.

- [ ] **Step 5: Commit context integration**

```powershell
git add legalai/packages/layers/analysis_pipeline.py legalai/packages/layers/deep_research.py legalai/tests/layers legalai/tests/jurisdictions/test_acceptance_hafta14.py
git commit -m "feat: route trade defense research context"
```

### Task 5: Add end-to-end acceptance coverage and documentation

**Files:**
- Create: `legalai/tests/jurisdictions/test_acceptance_ticaret_savunmasi.py`
- Modify: `docs/socratlegal-setup.md`

**Interfaces:**
- Consumes: `guess_jurisdictions`, `compose_persona_instructions`, and `build_reasoning_instructions`.
- Produces: a documented, testable user-visible capability.

- [ ] **Step 1: Write the acceptance test**

```python
from legalai.packages.jurisdictions.persona import compose_persona_instructions
from legalai.packages.jurisdictions.selection import guess_jurisdictions
from legalai.packages.layers.legal_reasoning import build_reasoning_instructions


def test_trade_defense_end_to_end_persona_and_reasoning():
    selection = guess_jurisdictions(
        "İhracatçı firma için dampinge karşı vergi soruşturmasında savunma stratejisi ve GTİP itirazı hazırlanacak."
    )
    assert selection.primary == "ticaret_savunmasi"

    persona = compose_persona_instructions([selection.primary], selection.expert_lenses)
    assert "gümrük" in persona.lower() or "damping" in persona.lower()

    reasoning = build_reasoning_instructions(
        [selection.primary], source_context="trade_defense_research"
    )
    assert "4. Cevap ve strateji nedir?" in reasoning
    assert "analysis-only" in reasoning
```

- [ ] **Step 2: Add one setup-documentation line**

Add the visible capability line: `Ticaret politikası savunması (damping, sübvansiyon, korunma tedbirleri — Türkiye birincil, AB/ABD/DTÖ karşılaştırmalı)`.

- [ ] **Step 3: Run the acceptance suite**

Run: `& 'C:\Users\hakan\Desktop\Yargi MCP Fork\legalai-yargi-mcp\.venv\Scripts\python.exe' -m pytest legalai/tests/jurisdictions legalai/tests/sources legalai/tests/layers -q`

Expected: PASS for the feature-area suite.

- [ ] **Step 4: Commit acceptance/docs changes**

```powershell
git add legalai/tests/jurisdictions/test_acceptance_ticaret_savunmasi.py docs/socratlegal-setup.md
git commit -m "test: verify trade defense persona flow"
```

### Task 6: Final verification and handoff

**Files:**
- Review: all files changed by Tasks 1-5.

- [ ] **Step 1: Run the complete test command and record collection status**

Run: `& 'C:\Users\hakan\Desktop\Yargi MCP Fork\legalai-yargi-mcp\.venv\Scripts\python.exe' -m pytest legalai/tests -q`

Expected: feature tests pass; if the pre-existing duplicate test-module collection error remains, report the exact two collisions separately rather than masking them.

- [ ] **Step 2: Run static checks available in the repository**

Run: `& 'C:\Users\hakan\Desktop\Yargi MCP Fork\legalai-yargi-mcp\.venv\Scripts\python.exe' -m compileall -q legalai`

Expected: exit code 0.

- [ ] **Step 3: Review diff and ASCII ref names**

Run: `git status --short; git diff --check; git branch --show-current`

Expected: branch is `feature/anti-damping-savunmasi`, `git diff --check` is clean, and no unrelated files changed.

- [ ] **Step 4: Use `superpowers:finishing-a-development-branch` for final integration options**

Do not push or merge automatically. Present the verified commit list and let the user choose local review, push, or PR integration.

