
# SocratLegal Ön Bilgi, Çapraz Yargı, Dilekçe ve Kalite Implementation Plan

> For agentic workers: REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Süreç başlatan belgelerden strateji ve bilgi-belge-delil listesi çıkaran, çapraz yargı etkilerini sorgulayan, kaynak/alıntı güvencesi olan ve persona uyumlu genel dilekçe işlemleri sunan SocratLegal altyapısını kurmak.

**Architecture:** Ortak quality policy, cross-domain inquiry, operational cards ve evidence ledger bütün analiz, mütalaa, strateji, sözleşme, bilirkişi ve dilekçe akışlarına bağlanır. Dilekçe işlemleri tek backend'de draft, review, shorten ve lengthen operasyonlarıdır; MCP'de keşfi kolaylaştıran ayrı araç adları bulunur. Yerel corpus ve canlı resmî adapter'lar federated arama ile çalışır; upstream public API'leri değiştirilmez.

**Tech Stack:** Python 3.11+, FastMCP, Pydantic, dataclasses, SQLite/FTS5, pypdf, optional Pillow/PyMuPDF/pytesseract OCR, pytest/pytest-asyncio, mevcut uv.lock ve portable installer.

## Global Constraints

- Superpowers, SocratLegal muhakemesini, persona profillerini, çapraz yargı sorgusunu veya kaynak sözleşmesini override edemez; yalnızca bunların eksiksiz ve ekonomik uygulanmasını denetler.
- Modelin basit alan promptu SocratLegal'in tam persona ve operasyonel perspektifinin yerine geçemez.
- Her çıktı analysis_only=true ve non_binding=true kalır.
- Erişilmeyen kaynak, karar, madde, doktrin görüşü, alıntı, süre veya olgu uydurulmaz.
- İddialar tam künye, belge kimliği, mümkünse madde/paragraf/sayfa ve erişilmiş kısa alıntıyla eşleştirilir.
- Kullanıcı belgeleri Git, genel corpus, telemetry veya temel model eğitimine yazılmaz; dış çağrıdan önce yerel PII masking uygulanır.
- Upstream modüller ve public API'ler doğrudan değiştirilmez; entegrasyon adapter üzerinden yapılır.
- TIFF/TIFF desteği yerel intake'te bulunur; OCR motoru yoksa ocr_required=true dönülür.
- Anti-damping bu planda aktif kaynak/persona değildir; yalnızca roadmap notudur.

---

### Task 1: Non-override kalite politikası ve çapraz yargı sorgusu

Files:
- Create: legalai/packages/layers/quality_policy.py
- Create: legalai/packages/layers/cross_domain_inquiry.py
- Modify: legalai/packages/layers/reasoning_playbook.py, legalai/packages/layers/legal_reasoning.py, legalai/packages/layers/quality_contract.py, legalai/packages/layers/pipeline.py, legalai/packages/layers/analysis_pipeline.py, legalai/packages/layers/grounded_generator.py
- Test: legalai/tests/layers/test_quality_policy.py, legalai/tests/layers/test_cross_domain_inquiry.py, legalai/tests/layers/test_reasoning_invariants.py

Interfaces:
- build_quality_context(jurisdiction_ids, expert_lenses, source_ids, operational_context=None, quality_profile="auto", model_hint="") -> str
- build_cross_domain_inquiry(question, jurisdiction_ids, documents=()) -> CrossDomainInquiry

Steps:
- [ ] Write failing tests asserting all four SocratLegal reasoning steps, complete persona IDs, positive/negative cross-domain branches, operational labels, source limits and explicit non-override language.
- [ ] Run and confirm failure: uv run --frozen pytest legalai/tests/layers/test_quality_policy.py legalai/tests/layers/test_cross_domain_inquiry.py legalai/tests/layers/test_reasoning_invariants.py -q
- [ ] Implement the policy and cross-domain dataclasses. Put SocratLegal reasoning/persona/source rules before the optimization kernel; create one effect record per detected jurisdiction and use only supplied document IDs.
- [ ] Wire the context through host instructions, Context.output_contract, grounded generation, deep research, opposing, contract and bilirkişi instructions without removing existing playbook/persona text.
- [ ] Run regression: uv run --frozen pytest legalai/tests/layers/test_reasoning_instructions.py legalai/tests/layers/test_grounded_generator.py -q
- [ ] Commit: git add legalai/packages/layers legalai/tests/layers; git commit -m "feat: enforce quality precedence and cross-domain inquiry"

### Task 2: Operational cards and evidence ledger

Files:
- Create: legalai/packages/layers/operational_cards.py, legalai/packages/layers/evidence_ledger.py
- Modify: legalai/packages/layers/operational_context.py, legalai/packages/layers/analysis_pipeline.py, legalai/packages/layers/grounded_generator.py, legalai/packages/layers/verified_citation_check.py, legalai/packages/shared/evidence.py
- Test: legalai/tests/layers/test_operational_cards.py, legalai/tests/layers/test_evidence_ledger.py

Interfaces:
- build_operational_cards(question, jurisdiction_ids, supplied_facts=()) -> tuple[OperationalCard, ...]
- build_evidence_ledger(claims, documents, source_evidence=()) -> tuple[EvidenceRecord, ...]
- validate_evidence_ledger(records) -> dict[str, Any]

Steps:
- [ ] Write failing tests for crypto, contract/market, technical-report and unknown contexts; test fact/sector/hypothesis labels and unsupported citation detection.
- [ ] Run and confirm failure: uv run --frozen pytest legalai/tests/layers/test_operational_cards.py legalai/tests/layers/test_evidence_ledger.py -q
- [ ] Implement cards for actors, normal workflow, incentives, technical traces, unlawful-pattern hypotheses and alternative explanations; every item receives a visible label.
- [ ] Implement EvidenceRecord with claim ID, source ID, source type, full citation, quote, pin, authority level, ratio/dictum, temporal note and relevance. Empty source bodies cannot produce quotes.
- [ ] Add ledger instructions and validation results to all host output contracts while preserving existing citation compatibility.
- [ ] Run: uv run --frozen pytest legalai/tests/layers/test_operational_cards.py legalai/tests/layers/test_evidence_ledger.py legalai/tests/layers/test_analysis_pipeline.py -q
- [ ] Commit: git add legalai/packages/layers legalai/packages/shared/evidence.py legalai/tests/layers; git commit -m "feat: add operational evidence cards and citation ledger"

### Task 3: Common document intake and TIFF support

Files:
- Create: legalai/packages/documents/__init__.py, legalai/packages/documents/intake.py
- Modify: legalai/packages/contracts/intake.py, legalai/packages/bilirkisi/workflow.py, pyproject.toml, uv.lock
- Test: legalai/tests/documents/test_intake.py, legalai/tests/contracts/test_intake.py, legalai/tests/bilirkisi/test_workflow.py

Interfaces:
- DocumentInput(text: str | None = None, file_path: Path | None = None)
- extract_document(value: DocumentInput, ocr_provider=None) -> ExtractedDocument

Steps:
- [ ] Write failing tests for TXT, PDF, DOCX, image, tif and tiff, including injected OCR success and no-engine ocr_required behavior.
- [ ] Run and confirm failure: uv run --frozen pytest legalai/tests/documents -q
- [ ] Extract the existing safe parsers into common intake; keep local PII masking and preserve contract/bilirkişi public dataclass fields.
- [ ] Add or lock the optional OCR dependency only if absent, regenerate uv.lock, and document Windows Tesseract plus Turkish language data.
- [ ] Run: uv run --frozen pytest legalai/tests/documents legalai/tests/contracts legalai/tests/bilirkisi -q
- [ ] Commit: git add legalai/packages/documents legalai/packages/contracts legalai/packages/bilirkisi pyproject.toml uv.lock legalai/tests; git commit -m "feat: unify document intake and TIFF support"

### Task 4: Process-triggering document intake and strategy

Files:
- Create: legalai/packages/layers/pre_action_strategy.py
- Test: legalai/tests/layers/test_pre_action_strategy.py
- Modify: legalai/apps/mcp/server.py, legalai/packages/discovery/catalog.py, docs/socratlegal-user-install.md, docs/mcp-client-setup.md

Interfaces:
- PreActionRequest(document_text, file_path, mode, question, jurisdiction_hint, event_dates)
- analyze_pre_action(request) -> PreActionResult

Steps:
- [ ] Write failing tests for tebligat, iddianame, administrative notice and unknown trigger; assert P0/P1/P2/P3 prioritization, missing-fact branches, cross-domain effects, evidence preservation and non-binding flags.
- [ ] Run and confirm failure: uv run --frozen pytest legalai/tests/layers/test_pre_action_strategy.py -q
- [ ] Implement local classification for sender/recipient, claims, relief, attachments, dates, procedural posture and uncertainty.
- [ ] Implement the information/document/evidence matrix and conditional strategies for response, objection, interim protection, mediation, settlement, 35/A, enforcement, institution/board applications and genuine-crime-report routes.
- [ ] Connect temporal context, forums, deadlines, cross-domain inquiry, operational cards and evidence ledger.
- [ ] Register socratlegal_onbilgi_ve_strateji plus aliases, catalog entry, parameter descriptions and natural-language examples.
- [ ] Run: uv run --frozen pytest legalai/tests/layers/test_pre_action_strategy.py legalai/tests/apps/test_mcp_discovery.py legalai/tests/apps/test_mcp_parameter_descriptions.py -q
- [ ] Commit: git add legalai/packages/layers/pre_action_strategy.py legalai/apps/mcp/server.py legalai/packages/discovery legalai/tests docs; git commit -m "feat: add process-triggering document strategy intake"

### Task 5: Shared general pleading backend and four operations

Files:
- Create: legalai/packages/petitions/__init__.py, legalai/packages/petitions/models.py, legalai/packages/petitions/service.py, legalai/packages/petitions/quality.py
- Test: legalai/tests/petitions/test_service.py
- Modify: legalai/apps/mcp/server.py, legalai/packages/discovery/catalog.py

Interfaces:
- PetitionOperation = draft | review | shorten | lengthen
- process_petition(request) -> PetitionResult

Steps:
- [ ] Write failing tests asserting sourced draft/review, safe shortening, context-preserving lengthening and Turkish-language lens metadata.
- [ ] Run and confirm failure: uv run --frozen pytest legalai/tests/petitions -q
- [ ] Implement one backend routing the four operations and always consuming quality policy, personas, cross-domain inquiry, operational cards, temporal context and evidence ledger.
- [ ] Implement shortening safeguards: classify paragraphs as essential, strategic, duplicative, optional or risky; never silently delete content concerning dava şartı, görev, kesin yetki, süre, delil or talep sonucu.
- [ ] Implement lengthening safeguards: add only retrieved norms, decisions, doctrine, counterarguments and operational links; reject out-of-scope facts.
- [ ] Add the Turkish language professor lens for clear, coherent Turkish without changing legal meaning or source level.
- [ ] Register socratlegal_dilekce_incele, socratlegal_dilekce_hazirla, socratlegal_dilekce_kisalt, socratlegal_dilekce_uzat and legacy aliases with descriptions.
- [ ] Run: uv run --frozen pytest legalai/tests/petitions legalai/tests/apps/test_mcp_parameter_descriptions.py legalai/tests/apps/test_mcp_branding.py -q
- [ ] Commit: git add legalai/packages/petitions legalai/apps/mcp/server.py legalai/packages/discovery legalai/tests; git commit -m "feat: add source-grounded general pleading operations"

### Task 6: Privacy-safe local pleading style profiles

Files:
- Create: legalai/packages/petitions/style_profile.py
- Test: legalai/tests/petitions/test_style_profile.py
- Modify: legalai/packages/petitions/models.py, legalai/apps/mcp/server.py, legalai/packages/discovery/catalog.py, docs/socratlegal-user-install.md

Interfaces:
- build_style_profile(example_texts, profile_id="local-default") -> StyleProfile

Steps:
- [ ] Write failing tests proving heading/citation/tone/argument-order signals are captured while raw examples and PII are absent from serialized profiles.
- [ ] Run and confirm failure: uv run --frozen pytest legalai/tests/petitions/test_style_profile.py -q
- [ ] Implement deterministic local extraction; do not fine-tune GPT/Claude/Codex or expose sample documents to general training.
- [ ] Add explicit user-consent selection to petition operations and document local persistence/clear behavior.
- [ ] Run petition regression and commit: git add legalai/packages/petitions legalai/apps/mcp/server.py legalai/packages/discovery legalai/tests docs; git commit -m "feat: add local pleading style profiles"

### Task 7: Reklam Kurulu corpus, adapter and persona

Files:
- Modify: legalai/packages/corpus/sources/registry.py, legalai/packages/corpus/sources/official.py, legalai/packages/corpus/federated.py, legalai/packages/jurisdictions/keywords.py, legalai/packages/discovery/catalog.py
- Create: legalai/configs/jurisdictions/reklam_kurulu.yaml
- Test: legalai/tests/corpus/test_reklam_kurulu_source.py, legalai/tests/jurisdictions/test_reklam_kurulu_persona.py

Steps:
- [ ] Write failing tests using injected official HTML fixtures; assert source ID, decision citation, URL, body and retrieval provenance.
- [ ] Run focused tests and confirm failure.
- [ ] Add reklam_kurulu registry descriptor and keyword gate without changing legal reasoning order.
- [ ] Implement the official adapter using the existing HTML collection pattern; unavailable pages produce source errors, never invented results.
- [ ] Add the persona for senior advertising lawyer, senior consumer lawyer, Advertising Board chair perspective and advertising-sector expert, with supporting hukuk/idare/ceza lenses when triggered.
- [ ] Run corpus/persona/federated tests and commit: git add legalai/packages/corpus legalai/configs/jurisdictions legalai/packages/jurisdictions legalai/packages/discovery legalai/tests; git commit -m "feat: add Reklam Kurulu corpus and persona"

### Task 8: Command dictionary and conditional visual specs

Files:
- Create: legalai/packages/discovery/commands.py, legalai/packages/discovery/visuals.py
- Modify: legalai/apps/mcp/server.py, legalai/packages/discovery/catalog.py, docs/mcp-client-setup.md, docs/socratlegal-user-install.md
- Test: legalai/tests/apps/test_mcp_command_dictionary.py, legalai/tests/apps/test_visual_specs.py

Interfaces:
- command_dictionary() -> dict[str, Any]
- visual_spec(kind, data) -> dict[str, Any]
- Resource URI: socratlegal://commands
- MCP tool: socratlegal_komut_sozlugu

Steps:
- [ ] Write failing tests for stable command IDs, aliases, resource discovery, tool descriptions and Mermaid/table fallback.
- [ ] Run and confirm failure.
- [ ] Implement dictionary/resource while preserving legacy aliases and stating that slash rendering depends on the host client.
- [ ] Implement visual specs only when the relationship is materially clearer than prose; always return a text/table fallback.
- [ ] Expose the tool/resource, update docs, run tests and commit: git add legalai/packages/discovery legalai/apps/mcp/server.py legalai/tests/apps docs; git commit -m "feat: add command dictionary and visual specs"

### Task 9: Portable all-IDE registration

Files:
- Modify: legalai/packages/installer/models.py, legalai/packages/installer/config_merge.py, legalai/packages/installer/paths.py, legalai/apps/cli/main.py, scripts/install.ps1, scripts/install.sh
- Test: legalai/tests/installer/test_all_ide_registration.py
- Modify: docs/socratlegal-user-install.md

Interfaces:
- CLI: socratlegal install --ide all --only-installed
- discover_supported_ides() -> tuple[IdeDescriptor, ...]
- register_all_installed_ides(...) -> InstallReport

Steps:
- [ ] Write failing tests for existing-client detection, backups, idempotency, unrelated server preservation and skipped-client reporting.
- [ ] Run and confirm failure: uv run --frozen pytest legalai/tests/installer/test_all_ide_registration.py -q
- [ ] Implement all through existing config merge/backup mechanisms; never overwrite user settings.
- [ ] Document registering a later-installed IDE without re-downloading the portable package.
- [ ] Run installer suite and commit: git add legalai/packages/installer legalai/apps/cli install.ps1 install.sh legalai/tests/installer docs; git commit -m "feat: support portable all-IDE registration"

### Task 10: Integration, documentation and release verification

Files:
- Create: legalai/tests/integration/test_pre_action_to_petition_flow.py, legalai/tests/integration/test_cross_domain_output_contract.py, legalai/tests/integration/test_reklam_kurulu_flow.py
- Modify: docs/socratlegal-setup.md, docs/socratlegal-user-install.md, docs/mcp-client-setup.md, legalai/packages/discovery/catalog.py

Steps:
- [ ] Write integration tests for synthetic tebligat to intake, question/document/evidence matrix, cross-domain strategy and petition operation; include indictment and advertisement fixtures.
- [ ] Run integration tests and confirm only expected pre-implementation failures.
- [ ] Apply only wiring fixes; do not alter upstream modules or user-owned IDE files.
- [ ] Run final verification: git diff --check; uv lock --check; uv run --frozen pytest legalai/tests -q
- [ ] Review public docs for privacy, non-binding, unavailable-source and OCR limits.
- [ ] Commit integration/docs changes: git add docs legalai/tests/integration legalai/packages/discovery; git commit -m "test: verify SocratLegal intake and pleading workflows"
- [ ] Stop before push and present exact commits, tests and user-owned-file warnings for push/merge approval.

## Handoff

After this plan is approved, execute it in the isolated worktree
C:/Users/hakan/Desktop/Yargi MCP Fork/legalai-yargi-mcp/.worktrees/socratlegal-quality
with subagent-driven development or executing-plans. Do not stage or modify
the main checkout's user-owned .cursor/mcp.json, workflow edits, .superpowers/
or tmp/ files.
