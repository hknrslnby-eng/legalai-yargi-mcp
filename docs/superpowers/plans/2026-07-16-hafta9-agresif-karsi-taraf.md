# Hafta 9 — Agresif Karşı Taraf ve Geniş Hukuki Çözüm Stratejisi Uygulama Planı

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Her görev checkbox ile takip edilir.

**Goal:** Week 9 `agresif_karsi_taraf` akışını; olay tarihleri ve yürürlükteki hukuk, zamanaşımı/hak düşürücü süre, görev-yetki ve zorunlu ön şartlar, içtihat/doktrin delil blokları ve dava dışı çözüm yollarını birlikte değerlendiren, host-model/API-key modelleriyle çalışan bir MCP/HTTP özelliğine dönüştürmek.

**Architecture:** `TemporalLegalContext` ve `EvidenceBlock` tüm analiz yüzeylerinde paylaşılır. `ForumAndDeadlineAnalyzer` usulî riskleri, `StrategicPathPlanner` ise dava, icra, idari/kurul başvurusu, ceza soruşturması, arabuluculuk, Avukatlık Kanunu m.35/A, sulh/feragat/ibra ve benzeri yolları koşullu alternatifler olarak üretir. `OpposingAnalysis` bu bağlamı red-team karşı argümanları, karşıt içtihat araması ve zayıf nokta tespitiyle birleştirir. MCP varsayılan olarak host-orchestrated veri paketi döndürür; API anahtarı varsa aynı sözleşme üzerinden sunucu sentezi yapılabilir.

**Tech Stack:** Python 3.11+, dataclasses/typing, Pydantic Settings, FastMCP, FastAPI, pytest/pytest-asyncio, mevcut `Pipeline`/`Context`/`Document` yapıları, OpenAI-uyumlu LLM istemcileri.

## Global Constraints

- Mevcut Week 7–8 çalışma ağacındaki kullanıcı değişiklikleri korunacak; `git reset`, `git checkout --` veya ilgisiz dosya temizliği yapılmayacak.
- Bu sprint ayrı hosting/server kurmayacak. Yerel STDIO MCP çalışması ve ileride remote transport eklenebilecek saf domain arayüzleri hazırlanacak.
- `.env`, API anahtarları, kişisel veri ve gerçek kullanıcı vakası fixture’ı commit edilmeyecek.
- Tarih hiç algılanamazsa `TemporalLegalContext`, “güncel hukuk başlangıç varsayımı” üretecek; tarih algılandı diye otomatik kesin sonuç vermeyecek.
- Her hukukî sonuç `analysis_only`, `non_binding`, `confidence`, `assumptions` ve `missing_facts` alanlarını taşıyacak. “Kesin”, “bağlayıcı”, “mutlaka” dili ve kesin süre garantisi üretilemeyecek.
- Kaynak iddiası `EvidenceBlock` olmadan dışarı verilmeyecek. Künye, kaynak türü, kısa ilgili alıntı, URL veya belge kimliği, yürürlük durumu ve güven seviyesi bulunacak; çelişen kaynaklar gizlenmeyecek.
- `source_scope` yalnızca `targeted`, `all`, `selected` değerlerini kabul edecek; seçili kapsam için açık kaynak kimliği listesi kullanılacak.
- Her üretim kodu değişikliğinden önce o davranışı gösteren başarısız test yazılacak; her görev sonunda hedefli test ve `git diff --check` çalıştırılacak.
- Sözleşme inceleme ve due diligence bu sprintte yalnızca ileri geliştirme sözleşmesi/backlog olarak kalacak; bu plan onların üretim kodunu uygulamaz.
- Codex kurulumu `.codex/config.toml` ile, Cursor kurulumu mevcut `.cursor/mcp.json` ile ayrı tutulacak; hiçbir görev mevcut Cursor sunucusunu, kullanıcı ayarlarını, global daemon/port durumunu veya sırları üzerine yazmayacak.

---

## Task 1 — Ortak domain sözleşmeleri ve hukuki güvenlik zarfı

**Files:**

- Create `legalai/packages/shared/evidence.py`
- Create `legalai/packages/shared/temporal.py`
- Modify `legalai/packages/layers/pipeline.py`
- Create `legalai/tests/shared/test_evidence_temporal_contracts.py`

**Interfaces:**

- `SourceScope = Literal["targeted", "all", "selected"]`
- `EvidenceBlock(claim, source_type, citation_key, full_citation, short_quote, source_url, document_id, temporal_status, relevance, confidence)`
- `DateObservation(label, value, precision, basis, confidence)`; `precision` is `day|month|year|unknown`.
- `TemporalLegalContext(event_dates, filing_dates, reference_dates, active_law_baseline, applicable_norms, superseded_norms, invalidation_events, deadline_risks, assumptions, missing_facts, confidence)`
- `LegalAnalysisEnvelope(analysis_only=True, non_binding=True, confidence, assumptions, missing_facts, evidence, source_scope)` with `to_dict()`.
- Add optional `temporal_context`, `evidence`, `strategy_options`, `forum_candidates` fields to `Context` without breaking current layers.

**TDD:**

1. Test that a complete `EvidenceBlock` serializes all citation and temporal fields, while missing `short_quote` is rejected.
2. Test `source_scope` validation and rejection of an unknown scope.
3. Test that an undated question creates a context with `active_law_baseline="current-law-assumption"`, an explicit assumption, and `missing_facts`.
4. Test that the envelope always serializes `analysis_only=true` and `non_binding=true`, including an empty-evidence result.
5. Run `uv run pytest legalai/tests/shared/test_evidence_temporal_contracts.py -q`; confirm initial failures, implement the dataclasses/validation, rerun green.

**Commit:** `feat: add shared legal analysis and evidence contracts`

## Task 2 — Provider router: explicit Gemini/OpenRouter/DeepSeek selection

**Files:**

- Modify `legalai/packages/shared/settings.py`
- Modify `legalai/packages/llm/router.py`
- Create `legalai/tests/llm/test_router_provider_selection.py`

**Interfaces:**

- Settings: `legalai_llm_provider: Literal["auto", "gemini", "openrouter", "deepseek", "groq"] = "auto"`, `openrouter_model`, `deepseek_model`, `gemini_model`, `groq_model`.
- `LLMRouter.route(task="simple"|"reasoning", provider=None)`: explicit provider wins; `auto` retains configured-provider fallback order.
- OpenRouter uses `https://openrouter.ai/api/v1`; DeepSeek uses `https://api.deepseek.com/v1`; model names come only from settings, with safe defaults and no hard-coded “v4 Pro” claim.
- Unsupported/unconfigured explicit provider raises `LLMNotConfiguredError` naming the missing setting, without exposing the secret.

**TDD:**

1. Test explicit OpenRouter and DeepSeek routes with fake settings and assert provider, base URL, model, and key attribute.
2. Test explicit Gemini route and `auto` fallback compatibility with existing Groq/Gemini/DeepSeek behavior.
3. Test model overrides and missing-provider error.
4. Run `uv run pytest legalai/tests/llm -q`; implement only after observing red tests; rerun green.

**Commit:** `feat: add configurable llm provider routing`

## Task 3 — Temporal source backend and date/legal-effect analyzer

**Files:**

- Create `legalai/packages/layers/temporal_context.py`
- Create `legalai/tests/layers/test_temporal_context.py`
- Modify `legalai/packages/layers/pipeline.py` only where Task 1 contracts require it

**Interfaces:**

- `TemporalSourceBackend` protocol: `async search_norms(query, on_date, scope) -> list[NormRecord]`, `async search_invalidation_events(query, date_from, date_to, scope) -> list[InvalEvent]`, `async search_procedural_rules(query, scope) -> list[NormRecord]`.
- `NormRecord(id, title, citation, effective_from, effective_to, status, source_url, quote, confidence)`.
- `InvalEvent(id, authority, decision_date, publication_date, effective_date, effect, affected_norm, citation, source_url, quote, confidence)`.
- `TemporalLegalContextBuilder.build(question, jurisdiction_hint=None, source_scope="targeted", selected_source_ids=None, backend=None) -> TemporalLegalContext`.
- `LimitationAndPreclusionAnalyzer.analyze(context, profile) -> list[DeadlineRisk]`, where each risk carries `kind=zamanaşımı|hak_düşürücü_süre|usulî_süre|başvuru_süresi`, trigger, candidate deadline, interrupt/suspend facts, uncertainty, evidence.
- Date extraction is deterministic and conservative: explicit ISO/Turkish dates and labeled facts are observations; inferred dates require `basis` and lower confidence. AYM deferred-effect and Danıştay/idare annulment/stay records are represented as events, not assumed effects.

**TDD:**

1. Test event date and suit date extraction, unknown-date fallback, and confidence lowering for partial dates.
2. Test norm selection at event date versus filing date, including an earlier norm ending before the event.
3. Test an annulment with deferred effective date and ensure the effect is applied only from `effective_date`.
4. Test limitation, forfeiture, and procedural deadline risks as conditional records with missing trigger facts.
5. Test backend failures produce traceable uncertainty rather than a fabricated norm.
6. Run `uv run pytest legalai/tests/layers/test_temporal_context.py -q`; implement red-green.

**Commit:** `feat: add temporal law and deadline analysis layer`

## Task 4 — Forum, authority and prerequisite analyzer

**Files:**

- Create `legalai/packages/layers/forum_analyzer.py`
- Create `legalai/tests/layers/test_forum_analyzer.py`
- Modify `legalai/packages/jurisdictions/base.py` if profile fields are needed
- Add/modify jurisdiction YAML fixtures under `legalai/packages/jurisdictions/profiles/` only after inspecting the existing loader

**Interfaces:**

- `ForumCandidate(kind, name, jurisdiction_basis, venue_basis, prerequisites, deadline_risks, evidence, confidence, assumptions)`; `kind=mahkeme|icra_dairesi|idari_kurum|kurul|arabuluculuk|tahkim`.
- `ForumAndDeadlineAnalyzer.analyze(question, context, profile, documents, source_scope, selected_source_ids) -> list[ForumCandidate]`.
- Candidate ranking is evidence-weighted and may return multiple alternatives; no field may be named `certain_forum` or imply a guarantee.
- Profile support includes `competent_forums`, `venue_rules`, `mandatory_prerequisites`, and `procedural_deadlines` while remaining backward-compatible with current YAML.

**TDD:**

1. Test that a jurisdiction profile yields ranked görevli/yetkili court alternatives and preserves uncertainty where facts are missing.
2. Test icra dairesi, administrative authority/board, mandatory mediation, and optional mediation as distinct candidates.
3. Test that prerequisite and deadline evidence is attached to the candidate, not emitted as unsupported prose.
4. Test conflicting forum signals are both retained with lower confidence.
5. Run `uv run pytest legalai/tests/layers/test_forum_analyzer.py -q`; implement red-green.

**Commit:** `feat: add evidence-backed forum and prerequisite analysis`

## Task 5 — Broad strategic path planner

**Files:**

- Create `legalai/packages/layers/strategy_planner.py`
- Create `legalai/tests/layers/test_strategy_planner.py`

**Interfaces:**

- `StrategicPath(kind, title, objective, prerequisites, steps, evidence, benefits, risks, reversibility, expected_next_action, confidence, assumptions)`.
- `StrategicPathPlanner.plan(question, position, temporal_context, forum_candidates, documents, source_scope, selected_source_ids) -> list[StrategicPath]`.
- Candidate catalog must cover, when factually relevant: negotiation; Avukatlık Kanunu m.35/A settlement record; sulh/feragat/ibra/borç yapılandırma; mandatory/optional mediation and enforceability; ordinary suit; enforcement; interim attachment/injunction; administrative application and rejection preservation; authority/board complaint/application; criminal complaint only where a concrete offence signal and lawful evidentiary purpose exist; consumer/KİK/Rekabet/KVKK/tahkim/other specialised routes according to jurisdiction.
- Criminal and evidence-gathering options must include misuse/retaliation/legal-privilege warnings and never encourage fabricated complaints.
- Planner returns at least two conditional options when facts permit, plus `missing_facts` when it cannot safely rank them.

**TDD:**

1. Test a debt fact pattern returns enforcement, negotiation/35-A or mediation, and suit as separate options with different prerequisites.
2. Test an administrative fact pattern returns application-before-suit where relevant and marks the rejection-preservation strategy as conditional.
3. Test a concrete offence signal adds a cautious criminal route; a vague “complain to get evidence” request does not.
4. Test sulh/feragat/ibra and mediation paths contain enforceability/effect risks and source blocks.
5. Test no dates still produces a current-law baseline strategy with explicit uncertainty.
6. Run `uv run pytest legalai/tests/layers/test_strategy_planner.py -q`; implement red-green.

**Commit:** `feat: add broad legal solution strategy planner`

## Task 6 — Week 9 opposing-side vertical slice

**Files:**

- Create `legalai/packages/layers/opposing.py`
- Create `legalai/tests/layers/test_opposing.py`
- Modify `legalai/packages/layers/pipeline.py`

**Interfaces:**

- `OpposingRoleMap.map(position, role, jurisdiction_id) -> RoleMapping` with supported roles `davacı|davalı|sanık|katılan|başvurucu|karşı_taraf|idare`.
- `RedTeamCounterArgs.generate(position, role_mapping, context, limit=5) -> list[CounterArgument]`.
- `RebuttingCaseSearch.search(counter_args, documents, source_scope, selected_source_ids, limit=3) -> list[EvidenceBlock]`.
- `WeakPointDetector.detect(position, counter_args, temporal_context, forum_candidates, strategy_paths) -> list[WeakPoint]`.
- `OpposingResult` contains `counter_arguments`, `rebutting_evidence`, `weak_points`, `temporal_context`, `deadline_risks`, `forum_candidates`, `strategy_options`, `evidence`, `assistant_instructions`, and the nonbinding envelope fields.
- `run_opposing(...)` composes the modules, preserves host-first behavior when `synthesize=False`, and uses `LLMRouter` only when server synthesis is explicitly requested and configured.

**TDD:**

1. Test plaintiff position -> exactly five bounded counterargument slots (or fewer with an explicit missing-evidence reason) and at most three rebutting decisions.
2. Test temporal, deadline, forum, and strategy data are present in the same result and source IDs remain traceable.
3. Test feature flag disabled returns a stable disabled result without running external search.
4. Test host mode has no LLM call and includes host instructions; server mode uses an injected fake LLM client.
5. Test an incomplete fact pattern returns conditional branches, assumptions, and missing facts instead of a single conclusion.
6. Run `uv run pytest legalai/tests/layers/test_opposing.py -q`; implement red-green.

**Commit:** `feat: implement week 9 opposing analysis workflow`

## Task 7 — Shared citations and host/HTTP result contracts

**Files:**

- Modify `legalai/packages/layers/analysis_pipeline.py`
- Modify `legalai/packages/layers/deep_research.py`
- Modify `legalai/apps/api/routes.py`
- Create `legalai/tests/api/test_opposing_routes.py`
- Modify/add `legalai/tests/layers/test_analysis_pipeline.py` and `test_deep_research.py`

**Interfaces and behavior:**

- Extend `AnalysisResult.to_dict()` and `DeepResearchResult.to_dict()` with `evidence`, `temporal_context`, `deadline_risks`, `forum_candidates`, `strategy_options`, `analysis_only`, `non_binding`, `confidence`, `assumptions`, `missing_facts`, and `source_scope` without removing existing keys.
- Add Pydantic `OpposingRequest` fields `question`, `position`, `role`, `jurisdiction_hint`, `source_scope`, `selected_source_ids`, `synthesize`; validate role/scope.
- Add `POST /api/v1/opposing` and `OpposingResponse` as a serialization wrapper around `run_opposing`; preserve the existing `/analyze` contract.
- `build_assistant_instructions()` must require inline citation künye/source type plus a short relevant quote by default, identify conflicts, state applicable dates, and end with the nonbinding analysis disclaimer.
- Use stable JSON-safe values for datetimes, dataclasses, and source records; never expose API keys.

**TDD:**

1. Test existing `/api/v1/analyze` response compatibility.
2. Test `/api/v1/opposing` request validation, host-mode response, evidence serialization, and disclaimer.
3. Test deep research output receives the same citation/evidence display rule.
4. Test host instructions reference all required fields and prohibit unsupported conclusions.
5. Run `uv run pytest legalai/tests/api legalai/tests/layers/test_analysis_pipeline.py legalai/tests/layers/test_deep_research.py -q`; implement red-green.

**Commit:** `feat: expose evidence-backed strategy results across surfaces`

## Task 8 — MCP tool and client configuration

**Files:**

- Modify `legalai/apps/mcp/server.py`
- Create `.codex/config.toml`
- Create `docs/mcp-client-setup.md`
- Create `legalai/tests/apps/test_mcp_opposing_tool.py`

**Interfaces and behavior:**

- Add FastMCP tool `agresif_karsi_taraf(question, position, role="davacı", jurisdiction_hint=None, source_scope="targeted", selected_source_ids=None) -> dict`.
- Tool description must say: host model can use its existing subscription (Codex/ChatGPT, Claude, Cursor, VS Code, Antigravity); server synthesis and OpenRouter/DeepSeek/Gemini API-key routing are optional; result is nonbinding analysis.
- Respect `ENABLE_AGGRESSIVE_OPPOSING`; use read-only/idempotent annotations because the tool only searches/analyzes.
- `.codex/config.toml` must configure project-scoped STDIO server `legalai` with a portable `uv run legalai-mcp` command and repository `cwd`; no absolute user-specific executable path or secret.
- It must coexist with the existing `.cursor/mcp.json`: do not rewrite or rename its `legalai`/`yargi-mcp-fork` entries, do not introduce a shared TCP port/global daemon, and add a config smoke test that parses both files independently.
- `docs/mcp-client-setup.md` must document project trust, restarting/new task, and equivalent STDIO snippets for Codex, Claude, Cursor, VS Code and Antigravity; API-key provider variables must be listed by name only.
- Do not claim a remote server exists; document remote transport as a future extension point.

**TDD:**

1. Test the MCP tool delegates to an injected `run_opposing` fake and returns the full result.
2. Test disabled flag response and no delegate call.
3. Test config parses as TOML and contains no secret-like values or machine-specific absolute paths.
4. Run `uv run pytest legalai/tests/apps/test_mcp_opposing_tool.py -q` and config smoke tests that parse `.codex/config.toml` plus the existing `.cursor/mcp.json` without mutation; implement red-green.

**Commit:** `feat: expose legalai opposing tool to codex and ide clients`

## Task 9 — Cross-surface integration and regression suite

**Files:**

- Create `legalai/tests/integration/test_week9_opposing_flow.py`
- Modify existing fixtures only when required for backward-compatible injection.
- Do not modify existing unrelated Week 7–8 tests to weaken assertions.

**TDD/verification:**

1. Build a deterministic fixture with an event date, filing date, superseded norm, deferred invalidation, limitation trigger, competing forums, debt facts, and a concrete-but-conditional settlement/mediation opportunity.
2. Run the same fixture through `run_opposing(synthesize=False)`, HTTP route, and MCP tool; assert equivalent domain fields and source IDs.
3. Assert a partial/undated fixture returns current-law baseline plus `missing_facts`, not a false historical claim.
4. Assert every path, deadline, forum, and counterargument is either evidence-backed or explicitly marked as an assumption/uncertainty.
5. Run the full suite: `uv run pytest -q`.
6. Run static/format checks available in the repository and `git diff --check`; inspect `git status --short` to confirm only intended files changed.

**Commit:** `test: verify week 9 strategy flow across clients`

## Task 10 — Documentation, plan alignment and final verification

**Files:**

- Modify `FORK-KAPSAMLI-PLAN.md` to mark Week 9 deliverables and add the approved future backlog entries for `ContractReview` and `DueDiligence` if they are not already present.
- Modify `README.md` only to link the client setup and explain local STDIO/API-key optional modes, if that information is currently absent.
- Do not duplicate the full design spec; link `docs/superpowers/specs/2026-07-16-hafta9-agresif-karsi-taraf-design.md`.

**Verification:**

1. Search documentation and output strings for unsupported certainty claims, missing disclaimer, and stale provider instructions.
2. Confirm examples use placeholders, not real keys.
3. Run `uv run pytest -q`, `git diff --check`, and the repository’s available lint/type checks.
4. Review the final diff against every acceptance criterion in the design spec; do not mark complete if a source, uncertainty, or client-surface rule is absent.

**Commit:** `docs: align roadmap with week 9 strategy features`

## Definition of Done

- `agresif_karsi_taraf` works over local STDIO MCP without requiring a server API key, and Codex project configuration is present.
- Gemini subscription host models work through the same host-first MCP flow; OpenRouter and DeepSeek are optional explicit server providers configured only through environment variables.
- Event/filing/other dates, current-law fallback, norm transitions, invalidation/stay events, limitation/forfeiture/procedural deadline risks, and forum alternatives appear as structured uncertainty-aware output.
- Strategy output goes beyond litigation and includes relevant settlement, AvK 35/A, sulh/feragat/ibra, mediation, enforcement, administrative/board, arbitration, interim relief, and carefully gated criminal routes.
- Case law/doctrine/statute claims carry künye, source type, short relevant quote, source identifier/URL, temporal status and confidence; IDE/host instructions require those blocks by default.
- Every surface states that output is analysis/research assistance, not binding legal opinion, certainty, official decision, or guarantee.
- Existing Week 7–8 tests remain green and no unrelated dirty changes are overwritten.
- Contract review and due diligence are recorded as future development items, not falsely presented as implemented.

## Task 11 — LegalAI tek server veri/backend köprüsü

**Files:**

- Create `legalai/packages/layers/legal_source_backend.py`
- Modify `legalai/packages/layers/opposing.py`
- Modify `legalai/packages/layers/temporal_context.py`
- Create `legalai/tests/layers/test_legal_source_backend.py`
- Extend `legalai/tests/layers/test_opposing.py` and `test_temporal_context.py` with injected fake backend cases

**Interfaces:**

- `IntegratedLegalSourceBackend` implements both decision retrieval and `TemporalSourceBackend`; its decision path uses existing `BedestenSearchBackend` and its norm/invalidation path uses the existing Anayasa norm-denetimi client plus Bedesten/Danıştay decision search.
- `RebuttingCaseSearch.search(counter_args, source_scope, selected_source_ids, limit=3) -> list[EvidenceBlock]` searches the connected decision backend automatically for the generated counterarguments.
- `run_opposing(..., document_backend=None, temporal_backend=None)` uses the integrated backend by default, while tests and future tenant-specific backends can inject fakes.
- Source/HTTP/MCP responses preserve backend failures as trace/assumption/missing-fact records and never turn a search failure into a legal conclusion.
- The original `yargi-mcp` process is not started by LegalAI and is not required for LegalAI’s base retrieval path.

**TDD:**

1. Test integrated decision search normalizes source, citation, body and document ID into `Document`/`EvidenceBlock`.
2. Test AYM norm decision records become temporal events with decision/publication/effect fields and unknown effective date when the source does not establish it.
3. Test opposing mode automatically calls the injected backend for the question and each counterargument and caps rebutting evidence at three.
4. Test backend failure returns counterarguments/strategy with explicit source uncertainty and no fabricated citation.
5. Run focused backend/opposing/temporal tests; if the local Python runtime is unavailable, record the exact environment error and run static import/config checks.

**Commit:** `feat: connect legalai strategy layers to legal source backends`

## Task 12 — Single-server acceptance and client smoke checks

**Files:**

- Modify `legalai/tests/integration/test_week9_opposing_flow.py`
- Modify `legalai/tests/apps/test_mcp_opposing_tool.py`
- Modify `docs/mcp-client-setup.md`

**Acceptance:**

- A user with only the `legalai` MCP registration receives basic Yargıtay/Danıştay-backed layered analysis and automatic opposing-case evidence.
- No test starts a remote server or requires a second MCP process.
- Cursor’s existing `.cursor/mcp.json` remains unchanged while Codex uses `.codex/config.toml`.
- Full test suite, static checks and an import smoke test are run before any push proposal.

**Commit:** `test: verify legalai single-server acceptance flow`
