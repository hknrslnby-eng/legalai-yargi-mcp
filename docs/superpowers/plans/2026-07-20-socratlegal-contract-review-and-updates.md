# SocratLegal Contract Review and Safe Update Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (\`- [ ]\`) syntax for tracking.

**Goal:** Add privacy-first, source-grounded contract review, improve shared legal/technical reasoning, and make portable updates discoverable through explicit GitHub Release metadata checks.

**Architecture:** New SocratLegal-only \`contracts\` modules parse and classify a local contract, route personas, build a structured review brief, and call the existing federated pipeline with strictly redacted retrieval queries. The host IDE model produces the final answer by default; optional server-side synthesis receives only strict-redacted text. Portable update checks read small GitHub Release JSON metadata and never download/apply an archive without an explicit user action.

**Tech Stack:** Python 3.11+, FastMCP, dataclasses, existing federated retriever, existing LLMRouter, httpx, Typer, pytest.

## Global Constraints

- Product name is **SocratLegal**; internal \`legalai\` names and compatibility aliases remain supported.
- Do not modify upstream module directories or public upstream APIs.
- No hosting, custom domain, remote MCP runtime, telemetry, or silent update installation.
- Contract files and private legal-opinion examples never enter Git, corpus storage, telemetry, release archives, or external requests unredacted.
- Due diligence is explicitly excluded.
- All results are \`analysis_only\`, \`non_binding\`, citation-aware, and disclose assumptions/missing facts.
- Local corpus and live Bedesten/official adapters continue searching together.
- Do not stage or edit user files such as \`.cursor/mcp.json\`, \`.superpowers/\`, or \`tmp/\`.

---

## File Structure

- Create: \`legalai/packages/layers/reasoning_playbook.py\` — abstract, privacy-safe reasoning policy with no private document text, names, facts, or identifiers.

- Create: \`legalai/packages/layers/operational_context.py\` — cautious sector/workflow hypotheses.
- Modify: \`legalai/packages/layers/legal_reasoning.py\`, \`legalai/packages/layers/analysis_pipeline.py\` — reusable reasoning/output structure.
- Create: \`legalai/packages/contracts/{__init__,models,privacy,intake,review}.py\` — private local contract workflow.
- Modify: \`legalai/packages/bilirkisi/workflow.py\` — technical research briefs and substantive-law linkage.
- Modify: \`legalai/apps/mcp/server.py\`, \`legalai/packages/discovery/catalog.py\` — public MCP surface/discovery.
- Modify: \`legalai/packages/installer/update.py\`, \`legalai/apps/cli/main.py\`, \`.github/workflows/portable-release.yml\` — explicit release checks.
- Modify: \`docs/socratlegal-user-install.md\`, \`README.md\` — plain-Turkish product guidance.
- Create/modify: \`legalai/tests/contracts/*.py\`, \`legalai/tests/layers/test_reasoning_instructions.py\`, \`legalai/tests/layers/test_analysis_pipeline.py\`, \`legalai/tests/bilirkisi/test_workflow.py\`, \`legalai/tests/apps/test_mcp_{discovery,contract_review}.py\`, \`legalai/tests/installer/{test_update,test_docs}.py\`.

### Task 1: Shared operational context and legal reasoning

The task must add a `ReasoningPlaybook` dataclass with `render() -> str`. Its only contents are abstract stages: issue/scope framing, chronology-fact-evidence separation, norm-element-fact mapping, contrary-view testing, temporal/source hierarchy checks, and executive-summary plus detailed source-grounded synthesis. It must not contain names, raw passages, factual narratives, or identifiers from the private sample documents.

**Files:**
- Create: \`legalai/packages/layers/operational_context.py\`
- Modify: \`legalai/packages/layers/legal_reasoning.py\`
- Modify: \`legalai/packages/layers/analysis_pipeline.py\`
- Test: \`legalai/tests/layers/test_reasoning_instructions.py\`
- Test: \`legalai/tests/layers/test_analysis_pipeline.py\`

**Interfaces:**
- Produces \`OperationalContextBuilder.build(question: str, jurisdiction_ids: Sequence[str]) -> OperationalContext\`.
- Extends \`build_reasoning_instructions(jurisdiction_ids: Sequence[str], expert_lenses: Sequence[str] = (), operational_context: OperationalContext | None = None, playbook: ReasoningPlaybook = REASONING_PLAYBOOK) -> str\`.
- Adds \`operational_context: dict[str, Any]\` to \`AnalysisResult.to_dict()\`.

- [ ] **Step 1: Write failing tests.**

\`\`\`python
def test_operational_context_labels_crypto_as_hypothesis():
    context = OperationalContextBuilder().build("Kripto cüzdanına yönlendirildim", ["ceza"])
    assert context.domain == "crypto_asset_operations"
    assert "kesin olgu değildir" in context.safety_note

def test_reasoning_requires_summary_and_detailed_findings():
    text = build_reasoning_instructions(["hukuk"])
    assert "Yönetici özeti" in text
    assert "operasyonel bağlam" in text
    assert "hipotez" in text
\`\`\`

- [ ] **Step 2: Run the tests to confirm failure.**

Run: \`uv run --frozen pytest legalai/tests/layers/test_reasoning_instructions.py -q\`  
Expected: FAIL because the builder and instructions do not yet exist.

- [ ] **Step 3: Implement the deterministic, non-assertive builder.**

\`\`\`python
@dataclass(frozen=True)
class OperationalContext:
    domain: str | None
    hypotheses: tuple[str, ...]
    unknowns: tuple[str, ...]
    safety_note: str = "Bu operasyonel çerçeve kesin olgu değildir; somut delil ile doğrulanmalıdır."

class OperationalContextBuilder:
    def build(self, question: str, jurisdiction_ids: Sequence[str] = ()) -> OperationalContext:
        if "kripto" in question.casefold() or "cüzdan" in question.casefold():
            return OperationalContext(
                "crypto_asset_operations",
                ("Aktarım zinciri, cüzdan kontrolü ve üçüncü kişi yönlendirmesi incelenmelidir.",),
                ("Cüzdan sahibi, transfer onayı ve platform kayıtları bilinmiyor.",),
            )
        return OperationalContext(None, (), ("Sektör/operasyon bilgisi somut girdiden ayrıştırılamadı.",))
\`\`\`

Pass the context into \`AnalysisResult\`; preserve the four existing legal steps and require a short executive summary, detailed findings, and explicitly labelled operational hypotheses.

- [ ] **Step 4: Run focused regression tests.**

Run: \`uv run --frozen pytest legalai/tests/layers/test_reasoning_instructions.py legalai/tests/layers/test_analysis_pipeline.py -q\`  
Expected: PASS; four-step reasoning remains intact.

- [ ] **Step 5: Commit.**

\`\`\`powershell
git add legalai/packages/layers/operational_context.py legalai/packages/layers/legal_reasoning.py legalai/packages/layers/analysis_pipeline.py legalai/tests/layers/test_reasoning_instructions.py legalai/tests/layers/test_analysis_pipeline.py
git commit -m "feat: add operational context to legal reasoning"
\`\`\`

### Task 2: Privacy-first local contract intake

**Files:**
- Create: \`legalai/packages/contracts/{__init__,models,privacy,intake}.py\`
- Test: \`legalai/tests/contracts/test_privacy.py\`
- Test: \`legalai/tests/contracts/test_intake.py\`

**Interfaces:**
- \`ContractReviewRequest(contract_text, file_path, purpose, position, detail_level, event_dates, jurisdiction_hint, server_side_synthesis)\`; exactly one of text/path is required.
- \`extract_contract(text: str | None = None, file_path: Path | None = None) -> ContractIntake\` accepts only local \`.txt\`, \`.md\`, \`.pdf\`, \`.docx\`.
- \`ContractPrivacyGate.redact(text) -> RedactionResult\` is in-memory and has \`persisted=False\`.

- [ ] **Step 1: Write failing tests.**

\`\`\`python
def test_contract_redaction_never_persists_direct_identifiers():
    result = ContractPrivacyGate().redact("Ayşe Yılmaz, TCKN 12345678901, TR1200010000")
    assert "12345678901" not in result.text
    assert "TR1200010000" not in result.text
    assert result.persisted is False

def test_contract_intake_reads_docx_and_signals_scanned_pdf(tmp_path):
    intake = extract_contract(file_path=make_docx(tmp_path, "MADDE 1 - Bedel"))
    assert intake.format == "docx"
    assert intake.clauses[0].number == "1"
    assert extract_contract(file_path=make_scanned_pdf(tmp_path)).ocr_required is True
\`\`\`

- [ ] **Step 2: Run tests to confirm failure.**

Run: \`uv run --frozen pytest legalai/tests/contracts/test_privacy.py legalai/tests/contracts/test_intake.py -q\`  
Expected: FAIL because the contracts package does not exist.

- [ ] **Step 3: Implement strict local extraction/redaction.**

\`\`\`python
class ContractPrivacyGate:
    def redact(self, text: str) -> RedactionResult:
        redacted = redact_identifiers(text)       # TCKN, VKN, IBAN, card, e-mail, phone
        redacted = redact_party_lines(redacted)   # Taraf/Adres/İmza labelled values
        redacted = redact_probable_people(redacted)
        return RedactionResult(text=redacted, persisted=False, warnings=())
\`\`\`

Use \`pypdf\` for digital PDFs and DOCX XML extraction; return \`ocr_required=True\` for a PDF with no extractable text. Segment Turkish/common foreign headings (\`MADDE\`, \`ARTICLE\`, \`SECTION\`), detect \`tr|foreign|mixed\` language and foreign elements (currency, country/address, governing law, arbitration). Never call \`PiiGateway._persist\` or write raw contract content to \`.data\`.

- [ ] **Step 4: Run tests.**

Run: \`uv run --frozen pytest legalai/tests/contracts/test_privacy.py legalai/tests/contracts/test_intake.py -q\`  
Expected: PASS; OCR is transparent and no privacy map is written.

- [ ] **Step 5: Commit.**

\`\`\`powershell
git add legalai/packages/contracts legalai/tests/contracts/test_privacy.py legalai/tests/contracts/test_intake.py
git commit -m "feat: add private local contract intake"
\`\`\`

### Task 3: Contract qualification, persona routes, and risk/gap matrix

**Files:**
- Modify: \`legalai/packages/contracts/models.py\`
- Create/modify: \`legalai/packages/contracts/review.py\`
- Test: \`legalai/tests/contracts/test_review.py\`

**Interfaces:**
- \`classify_contract(intake) -> ContractClassification\` includes \`legal_nature\`, \`classification_method\`, \`foreign_law_layer\`, \`confidence\`.
- \`route_personas(classification: ContractClassification, intake: ContractIntake) -> tuple[PersonaRouteDecision, ...]\` includes invoked and negative reasons.
- \`build_issue_matrix(intake: ContractIntake, classification: ContractClassification, routes: tuple[PersonaRouteDecision, ...]) -> tuple[ContractIssue, ...]\` records clause, risk, missing point, legal/operational rationale, and personas.

- [ ] **Step 1: Write failing tests.**

\`\`\`python
def test_mixed_contract_uses_dominant_element_and_mohuk_priority():
    intake = intake_for("ARTICLE 1 Distribution; English law; EUR payment; exclusive territory")
    result = classify_contract(intake)
    assert result.legal_nature == "mixed_distribution"
    assert result.classification_method == "dominant_element"
    assert result.foreign_law_layer == "mohuk_priority"

def test_router_has_negative_reason_for_non_invoked_kvkk():
    kvkk = next(x for x in route_personas(classification_for_sale(), intake_for("MADDE 1 Satış bedeli")) if x.persona_id == "kvkk")
    assert kvkk.invoked is False
    assert kvkk.negative_reasons
\`\`\`

- [ ] **Step 2: Run the test file.**

Run: \`uv run --frozen pytest legalai/tests/contracts/test_review.py -q\`  
Expected: FAIL because qualification and route decisions do not exist.

- [ ] **Step 3: Implement deterministic classification/checklists.**

\`\`\`python
def classify_contract(intake: ContractIntake) -> ContractClassification:
    signals = score_contract_types(intake.text)
    legal_nature = choose_type_or_mixed(signals)
    return ContractClassification(
        legal_nature=legal_nature,
        classification_method="dominant_element" if legal_nature.startswith("mixed_") else "typical_contract",
        foreign_law_layer="mohuk_priority" if intake.foreign_element else "not_triggered",
        tbk_19_warning="Başlık yerine gerçek ortak irade ve edim dengesi değerlendirilir.",
        confidence=signals.confidence,
    )
\`\`\`

Route \`hukuk,idare,ceza,vergi,rekabet,kvkk,kik,sigorta,anayasa,insan_haklari\` only when triggered, while preserving reasons for non-invocation. Check parties/authority, object/performance, price, term, termination, liability, evidence/notice, confidentiality/data, IP, disputes, assignment, force majeure, invalidity and entire agreement; add specialized checks only on an actual trigger.

- [ ] **Step 4: Run tests.**

Run: \`uv run --frozen pytest legalai/tests/contracts/test_review.py -q\`  
Expected: PASS; foreign element puts MÖHUK above ordinary clause analysis.

- [ ] **Step 5: Commit.**

\`\`\`powershell
git add legalai/packages/contracts/models.py legalai/packages/contracts/review.py legalai/tests/contracts/test_review.py
git commit -m "feat: add contract qualification and persona routing"
\`\`\`

### Task 4: Federated evidence and bilingual review result

**Files:**
- Modify: \`legalai/packages/contracts/review.py\`
- Test: \`legalai/tests/contracts/test_review.py\`

**Interfaces:**
- \`async review_contract(request, pipeline_runner=run_pipeline) -> ContractReviewResult\`.
- Result has \`executive_summary, classification, persona_routes, clause_findings, gap_findings, evidence, temporal_context, operational_context, assistant_instructions, privacy, analysis_only, non_binding\`.

- [ ] **Step 1: Write failing tests.**

\`\`\`python
@pytest.mark.asyncio
async def test_review_queries_sources_with_redacted_text_only():
    seen = []
    async def fake_pipeline(question, **kwargs):
        seen.append(question)
        return analysis_result_with_document("d-1")
    result = await review_contract(request_for("Ayşe Yılmaz TCKN 12345678901 MADDE 1 Bedel"), fake_pipeline)
    assert "12345678901" not in seen[0]
    assert result.evidence[0]["doc_id"] == "d-1"

@pytest.mark.asyncio
async def test_foreign_contract_requests_bilingual_revision():
    result = await review_contract(request_for("ARTICLE 4 Governing law: English law"), fake_pipeline)
    assert "source_language_revision" in result.assistant_instructions
    assert "Turkish counterpart" in result.assistant_instructions
\`\`\`

- [ ] **Step 2: Run the test file.**

Run: \`uv run --frozen pytest legalai/tests/contracts/test_review.py -q\`  
Expected: FAIL because orchestration is absent.

- [ ] **Step 3: Implement source-grounded orchestration.**

\`\`\`python
async def review_contract(request: ContractReviewRequest, pipeline_runner=run_pipeline) -> ContractReviewResult:
    intake = extract_contract(text=request.contract_text, file_path=request.file_path)
    redacted = ContractPrivacyGate().redact(intake.text)
    classification = classify_contract(intake)
    routes = route_personas(classification, intake)
    issues = build_issue_matrix(intake, classification, routes)
    query = build_masked_research_query(redacted.text, classification, issues)
    evidence = await pipeline_runner(query, mode="layered", jurisdiction_hint=request.jurisdiction_hint, synthesize=False)
    return compose_review_result(intake, classification, routes, issues, evidence, request)
\`\`\`

Keep detailed clause/gap findings plus a concise executive summary. Legal propositions must be supported by the returned evidence; operational points remain hypotheses. For a foreign-language contract, instructions require a source-language suggested wording with a Turkish legal-terminology counterpart side-by-side. No raw contract text is sent to a federated adapter; optional server synthesis receives only the same strict-redacted content.

- [ ] **Step 4: Run tests.**

Run: \`uv run --frozen pytest legalai/tests/contracts/test_review.py legalai/tests/layers/test_analysis_pipeline.py -q\`  
Expected: PASS; returned evidence keeps provenance and no direct identifier reaches retrieval.

- [ ] **Step 5: Commit.**

\`\`\`powershell
git add legalai/packages/contracts/review.py legalai/tests/contracts/test_review.py
git commit -m "feat: add source-grounded contract review workflow"
\`\`\`

Before Task 5 implementation, define these concrete interfaces: `DomainInference(domain: str | None, confidence: float, evidence: tuple[str, ...])`; `infer_technical_domain(report_text: str, supplied_domain: str = "") -> DomainInference`; `TechnicalResearchBrief(technical_questions: tuple[str, ...], alternative_hypotheses: tuple[str, ...], required_materials: tuple[str, ...], legal_issue_links: tuple[str, ...], research_instructions: tuple[str, ...])`; and `link_substantive_issues(question: str, domain: DomainInference) -> tuple[str, ...]`.

### Task 5: Bilirkişi technical research briefs and substantive links

**Files:**
- Modify: \`legalai/packages/bilirkisi/workflow.py\`
- Modify: \`legalai/apps/mcp/server.py\`
- Test: \`legalai/tests/bilirkisi/test_workflow.py\`

**Interfaces:**
- \`infer_technical_domain(report_text, supplied_domain="") -> DomainInference\`.
- Extend \`ReportClaim\` with \`technical_questions, alternative_hypotheses, legal_issue_links, research_instructions\`.
- Keep technical assertions reviewable hypotheses; only legal propositions may cite retrieved legal evidence.

- [ ] **Step 1: Write a failing technical-depth test.**

\`\`\`python
@pytest.mark.asyncio
async def test_report_analysis_infers_domain_and_substantive_links():
    result = await analyze_report(
        text="Yangın yükü hesabında numune alma ve kalibrasyon açıklanmamıştır.",
        question="Sigorta tazminatına etkisini incele.",
    )
    claim = result.claims[0]
    assert result.technical_domain == "fire_safety_engineering"
    assert claim.alternative_hypotheses
    assert any("sigorta" in item.casefold() for item in claim.legal_issue_links)
    assert "teknik uzman görüşü değildir" in result.assistant_instructions
\`\`\`

- [ ] **Step 2: Run it to confirm failure.**

Run: \`uv run --frozen pytest legalai/tests/bilirkisi/test_workflow.py -q\`  
Expected: FAIL because current counterarguments are generic.

- [ ] **Step 3: Implement the research brief.**

\`\`\`python
def build_claim_brief(excerpt: str, domain: DomainInference, question: str) -> TechnicalResearchBrief:
    return TechnicalResearchBrief(
        technical_questions=("Yöntem tekrar üretilebilir mi?", "Ölçüm belirsizliği nedir?"),
        alternative_hypotheses=("Ham veri veya kalibrasyon eksikliği sonucu değiştirebilir.",),
        required_materials=("ham veri", "yöntem standardı", "kalibrasyon/numune kayıtları"),
        legal_issue_links=link_substantive_issues(question, domain),
    )
\`\`\`

Use \`compose_persona_instructions\` with the \`sigorta\` profile and detected technical lenses where triggered. Preserve HMK m.266 and m.279–281 as procedure anchors, then add only question/source-supported substantive legal links. The MCP payload gives the host model a detailed technical research brief, so it can use its own broad technical capability without presenting its conclusions as an expert report.

- [ ] **Step 4: Run regression tests.**

Run: \`uv run --frozen pytest legalai/tests/bilirkisi/test_workflow.py legalai/tests/apps/test_mcp_opposing_tool.py -q\`  
Expected: PASS; technical alternatives, evidence gaps, and legal boundaries are exposed.

- [ ] **Step 5: Commit.**

\`\`\`powershell
git add legalai/packages/bilirkisi/workflow.py legalai/apps/mcp/server.py legalai/tests/bilirkisi/test_workflow.py
git commit -m "feat: enrich expert report research briefs"
\`\`\`

### Task 6: Contract-review MCP tool and discoverability

**Files:**
- Modify: \`legalai/apps/mcp/server.py\`
- Modify: \`legalai/packages/discovery/catalog.py\`
- Modify: \`legalai/tests/apps/test_mcp_discovery.py\`
- Create: \`legalai/tests/apps/test_mcp_contract_review.py\`

**Interfaces:**
- Register \`socratlegal_sozlesme_incele(contract_text=None, file_path=None, purpose="", position="", detail_level="standard", event_dates=None, jurisdiction_hint=None, server_side_synthesis=False) -> dict\`.
- Register \`legalai_sozlesme_incele\` as an exact compatibility alias.

- [ ] **Step 1: Write failing MCP and catalog tests.**

\`\`\`python
@pytest.mark.asyncio
async def test_contract_tool_returns_non_binding_payload(monkeypatch):
    monkeypatch.setattr(server_module, "review_contract", fake_review_contract)
    payload = await server_module._socratlegal_contract_review_tool.fn(contract_text="MADDE 1 Bedel")
    assert payload["analysis_only"] is True
    assert payload["non_binding"] is True

def test_catalog_marks_contract_review_active():
    catalog = capability_catalog()
    assert catalog["active_public_tools"]["socratlegal_sozlesme_incele"] == "sozlesme_incele"
\`\`\`

- [ ] **Step 2: Run the focused tests.**

Run: \`uv run --frozen pytest legalai/tests/apps/test_mcp_contract_review.py legalai/tests/apps/test_mcp_discovery.py -q\`  
Expected: FAIL because no public tool/catalog item exists.

- [ ] **Step 3: Add tool aliases and clear discovery text.**

\`\`\`python
@app.tool(name="socratlegal_sozlesme_incele", description="Sözleşmeyi gizlilik, persona, kaynak ve madde bazında inceler.")
async def _socratlegal_contract_review_tool(
    contract_text: str | None = None,
    file_path: str | None = None,
    purpose: str = "",
    position: str = "",
    detail_level: str = "standard",
    event_dates: list[str] | None = None,
    jurisdiction_hint: str | None = None,
    server_side_synthesis: bool = False,
) -> dict:
    request = ContractReviewRequest(contract_text, file_path, purpose, position, detail_level, event_dates, jurisdiction_hint, server_side_synthesis)
    return (await review_contract(request)).to_dict()

@app.tool(name="legalai_sozlesme_incele", description="Geçiş uyumluluğu: SocratLegal sözleşme inceleme.")
async def _legacy_contract_review_tool(
    contract_text: str | None = None,
    file_path: str | None = None,
    purpose: str = "",
    position: str = "",
    detail_level: str = "standard",
    event_dates: list[str] | None = None,
    jurisdiction_hint: str | None = None,
    server_side_synthesis: bool = False,
) -> dict:
    return await _socratlegal_contract_review_tool.fn(contract_text, file_path, purpose, position, detail_level, event_dates, jurisdiction_hint, server_side_synthesis)
\`\`\`

Expose the active tool in \`legalai_yardim\`, provide a natural-language example, and remove the duplicated garbled bilirkişi planned item. Do not delete existing Legacy aliases.

- [ ] **Step 4: Run MCP/discovery tests.**

Run: \`uv run --frozen pytest legalai/tests/apps/test_mcp_contract_review.py legalai/tests/apps/test_mcp_discovery.py -q\`  
Expected: PASS; nontechnical users can discover the feature.

- [ ] **Step 5: Commit.**

\`\`\`powershell
git add legalai/apps/mcp/server.py legalai/packages/discovery/catalog.py legalai/tests/apps/test_mcp_contract_review.py legalai/tests/apps/test_mcp_discovery.py
git commit -m "feat: expose SocratLegal contract review tool"
\`\`\`

### Task 7: Explicit GitHub Release update discovery and documentation

The public MCP surface must expose `socratlegal_guncelleme_kontrol` as a metadata-only, read-only tool that delegates to the same checker as the CLI. It reports current version, available version, release notes URL, archive URL, checksum, and `auto_apply: false`; it never downloads an archive.

**Files:**
- Modify: \`legalai/packages/installer/update.py\`
- Modify: \`legalai/apps/cli/main.py\`
- Modify: \`legalai/apps/mcp/server.py\`
- Modify: \`.github/workflows/portable-release.yml\`
- Modify: \`docs/socratlegal-user-install.md\`, \`README.md\`
- Test: \`legalai/tests/installer/test_update.py\`, \`legalai/tests/installer/test_docs.py\`
- Test: \`legalai/tests/apps/test_mcp_update_check.py\`

**Interfaces:**
- \`default_manifest_url(platform_tag) -> str\` returns \`https://github.com/hknrslnby-eng/legalai-yargi-mcp/releases/latest/download/release-manifest-{platform_tag}.json\`; supported tags are \`windows-x64\`, \`macos-arm64\`, \`macos-x64\`, and \`linux-x64\`.
- \`fetch_release_manifest(url: str, get: Callable[[str], bytes]) -> dict[str, object]\` accepts HTTPS, maximum 1 MiB JSON object only.
- \`check_remote_update(current_version: str, manifest_url: str, get: Callable[[str], bytes], state_path: Path) -> UpdateCheckResult\` performs metadata-only comparison and 24-hour caching.
- CLI: \`socratlegal update check [--manifest-url URL | --manifest-file PATH] [--platform-tag TAG]\`.

- [ ] **Step 1: Write failing safety and documentation tests.**

\`\`\`python
def test_remote_manifest_is_https_only_and_never_fetches_archive(tmp_path):
    calls = []
    result = check_remote_update("1.0.0", "https://example.test/manifest.json", calls.append, state_path=tmp_path / "state.json")
    assert result.available is True
    assert calls == ["https://example.test/manifest.json"]
    with pytest.raises(UpdateError):
        fetch_release_manifest("http://example.test/manifest.json")

def test_docs_explain_check_then_explicit_apply():
    text = INSTALL_DOC.read_text(encoding="utf-8")
    assert "otomatik olarak indirmez" in text
    assert "GitHub Releases" in text
    assert "socratlegal_sozlesme_incele" in text

@pytest.mark.asyncio
async def test_update_mcp_tool_is_metadata_only(monkeypatch):
    async def fake_update_check(*args, **kwargs):
        return {"current_version": "1.0.0", "available_version": None, "auto_apply": False, "archive_downloaded": False}
    monkeypatch.setattr(server_module, "check_remote_update", fake_update_check)
    result = await server_module._socratlegal_update_check_tool.fn()
    assert result["auto_apply"] is False
    assert result["archive_downloaded"] is False
\`\`\`

- [ ] **Step 2: Run installer tests.**

Run: \`uv run --frozen pytest legalai/tests/installer/test_update.py legalai/tests/installer/test_docs.py -q\`  
Expected: FAIL because only a local manifest file is currently supported.

- [ ] **Step 3: Implement metadata-only checks and accurate docs.**

\`\`\`python
def fetch_release_manifest(url: str, get: Callable[[str], bytes] = _http_get) -> dict[str, object]:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise UpdateError("Release metadata adresi HTTPS olmalıdır.")
    raw = get(url)
    if len(raw) > 1024 * 1024:
        raise UpdateError("Release metadata boyutu sınırı aşıldı.")
    payload = json.loads(raw.decode("utf-8"))
    if not isinstance(payload, dict):
        raise UpdateError("Release metadata JSON nesnesi olmalıdır.")
    return payload
\`\`\`

Use a local file only when explicitly passed; otherwise resolve the platform manifest URL and use the existing 24-hour cache. Print version/release/checksum and “no archive downloaded”. Keep \`update apply\` checksum-gated and separate. The release workflow must publish predictable per-platform manifest assets. Docs must describe: check → user downloads/approves archive → apply → rollback; checkout users use \`git pull\`, \`uv sync --frozen\`, IDE reload. State only Gemini, OpenRouter, DeepSeek, and Groq are presently routed server-side; an IDE subscription is host-model access, not a transmitted SocratLegal credential.

- [ ] **Step 4: Run installer/documentation tests.**

Run: \`uv run --frozen pytest legalai/tests/installer/test_update.py legalai/tests/installer/test_docs.py -q\`  
Expected: PASS; no documents are sent and no update is silently installed.

- [ ] **Step 5: Commit.**

\`\`\`powershell
git add legalai/packages/installer/update.py legalai/apps/cli/main.py legalai/apps/mcp/server.py .github/workflows/portable-release.yml docs/socratlegal-user-install.md README.md legalai/tests/installer/test_update.py legalai/tests/installer/test_docs.py
git commit -m "feat: add explicit portable update discovery"
\`\`\`

### Task 8: Full verification and handoff

**Files:**
- Modify only the smallest relevant file if a verification check identifies a real defect.

- [ ] **Step 1: Run the complete locked test suite.**

Run: \`uv run --frozen pytest -q\`  
Expected: PASS; record total tests and warnings.

- [ ] **Step 2: Verify diff and portable privacy boundaries.**

Run: \`git diff --check\`  
Expected: no output, exit code 0.

Run: \`uv run --frozen pytest legalai/tests/installer/test_packaging.py legalai/tests/installer/test_portable_layout.py -q\`  
Expected: PASS; portable archives exclude \`.env\`, data, databases, IDE settings, and private documents.

- [ ] **Step 3: Review the intended change set.**

Run: \`git status --short\`  
Expected: SocratLegal source/tests/docs/workflow changes only; user-owned \`.cursor/mcp.json\`, \`.superpowers/\`, and \`tmp/\` remain untouched.

- [ ] **Step 4: Commit only a verified corrective change, if needed.**

\`\`\`powershell
If a verification failure reveals a real defect, stop the handoff, patch only the exact failing files, rerun the failed test and the full suite, then create a separate focused commit whose message names the defect. Do not create a corrective commit merely to mark verification.
\`\`\`

- [ ] **Step 5: Present evidence and request GitHub push authorization.**

Report tests, commits, tool names, update behavior, and the required IDE reload for checkout users. Do not push, merge, or alter the upstream repository without explicit user approval.
