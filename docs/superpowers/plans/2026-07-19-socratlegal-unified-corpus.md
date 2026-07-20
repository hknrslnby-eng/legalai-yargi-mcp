# SocratLegal Unified Corpus Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the fork into a self-contained SocratLegal MCP server whose public tool surface exposes the approved analysis capabilities and whose retrieval layer federates the local corpus with live official/primary-source adapters, without modifying the upstream module contracts.

**Architecture:** Keep `legalai` as the local Python package and add `socratlegal_*` public MCP aliases. Add a separate corpus domain under `legalai/packages/corpus` with a local SQLite/FTS5 store, source registry, provenance-preserving records, and parallel local/live retrieval. Wrap existing upstream clients through adapters rather than rewriting upstream modules. Route every grounded analysis surface and the bilirkişi workflow through the federated backend. Keep corpus data and PII maps outside Git.

**Tech Stack:** Python 3.11+, FastMCP, Pydantic/dataclasses, SQLite/FTS5 via aiosqlite, existing `uv` environment, pytest/pytest-asyncio, existing Bedesten/official source clients.

## Global Constraints

- [ ] Do not edit, rename, or delete files in the upstream-derived root modules unless an adapter boundary cannot otherwise be implemented; preserve their public contracts and tests.
- [ ] Do not edit the user-local `.cursor/mcp.json` automatically. Repository examples and instructions may be updated; local renaming remains an explicit user action.
- [ ] Do not commit `.data/`, extracted documents, PII maps, API keys, or provider responses.
- [ ] Query local corpus and live official adapters concurrently. Local availability must never suppress Yargıtay, Danıştay, AYM, AİHM/HUDOC, Bedesten, or other configured primary sources.
- [ ] Institutional corpus development order is an ingestion/adapter priority only; it must not become a legal-authority ranking in reasoning.
- [ ] Every corpus hit carries source identity, document/revision identity, retrieval mode, URL/citation, date/effective-date metadata when known, and an uncertainty/availability status.
- [ ] Missing credentials or unavailable sites degrade source-by-source and never crash the whole federated search.
- [ ] All new production behavior is preceded by a focused failing test; run the smallest relevant test first, then the full suite.

---

## Task 1: Public SocratLegal branding and compatibility aliases

**Files:** `legalai/apps/mcp/server.py`, `legalai/packages/discovery/catalog.py`, focused MCP/catalog tests, repository setup documentation.

- [ ] Write failing tests asserting the public server capability metadata uses `SocratLegal`, exposes `socratlegal_katmanli_analiz`, `socratlegal_agresif_karsi_taraf`, `socratlegal_derin_arastirma`, `socratlegal_bilirkisi_raporu_analiz`, and `socratlegal_bilirkisi_raporu_dilekce`, while legacy `legalai_*` names remain callable aliases.
- [ ] Implement public aliases and update capability/help text without removing existing registrations.
- [ ] Add IDE/CLI configuration examples for stdio installation and explicitly document that the local package path may remain `legalai`.
- [ ] Run the focused server/catalog tests.

## Task 2: Corpus domain model, local store, and FTS search

**Files:** `legalai/packages/corpus/models.py`, `legalai/packages/corpus/store.py`, `legalai/packages/shared/settings.py`, corpus unit tests.

- [ ] Write failing tests for source/document/revision/chunk/citation records, idempotent upsert by content hash, FTS search, sync cursors, and source availability metadata.
- [ ] Implement the SQLite schema (`source_registry`, `corpus_documents`, `corpus_revisions`, `corpus_chunks`, `corpus_fts`, `corpus_citations`, `sync_cursors`) with async-safe initialization and parameterized queries.
- [ ] Add a configurable `corpus_db_path` defaulting to `.data/socratlegal_corpus.db`; preserve existing database settings.
- [ ] Add deterministic chunking/content hashing and provenance-preserving result conversion.
- [ ] Run corpus unit tests.

## Task 3: Federated source contracts and parallel retrieval

**Files:** `legalai/packages/corpus/adapters.py`, `legalai/packages/corpus/federated.py`, source-policy/config files, corpus integration tests.

- [ ] Write failing tests with fake local/live adapters proving concurrent fan-out, failure isolation, deterministic deduplication, source provenance, and no local-first suppression.
- [ ] Implement `SourceAdapter`, `LocalCorpusAdapter`, `FederatedRetriever`, result status/error models, and bounded concurrency/timeouts.
- [ ] Register primary and secondary source families, retaining live Bedesten and AİHM/HUDOC paths even when no local corpus exists.
- [ ] Extend source policy/configuration for Rekabet, KVKK, KİK, TİHEK, KDK, secondary regulators, OECD, EU Commission/CJEU, and public doctrine without changing authority semantics.
- [ ] Run corpus integration tests.

## Task 4: Official-source adapters and corpus synchronization

**Files:** new adapter modules under `legalai/packages/corpus/sources/`, source registry tests, sync command/module, secret-handling tests.

- [ ] Write failing adapter contract tests using fake clients for Rekabet (decisions, regulations, guides, sector reports), KVKK (board/principle decisions and guides), KİK, TİHEK, and KDK.
- [ ] Implement wrappers around existing upstream client modules; convert responses to corpus records and leave the upstream client files untouched.
- [ ] Add secondary registrations/adapters for BDDK, SPK, BTK, RTÜK, EPDK, KGK, GİB, Sayıştay, Sigorta Tahkim, Uyuşmazlık, Emsal, Yargıtay, Danıştay, AYM, and Bedesten where existing clients permit safe delegation.
- [ ] Make optional provider-token sources unavailable unless configured through environment/settings; never use or expose hard-coded fallback secrets in the new path.
- [ ] Implement resumable `corpus sync --source all|<source>` and `corpus status` entry points with dry-run and bounded request behavior; tests must use mocked transport.
- [ ] Run adapter and sync tests.

## Task 5: Route legal analysis, temporal context, and strategy through the federated backend

**Files:** `legalai/packages/layers/legal_source_backend.py`, retrieval/temporal integration points, existing analysis tests.

- [ ] Write failing tests proving layered analysis, opposing-party analysis, deep research, and solution-strategy output receive local-plus-live corpus hits and preserve citation/authority/temporal metadata.
- [ ] Implement a compatibility backend that delegates to the federated retriever while preserving `DocumentSearchBackend`, Bedesten behavior, AYM invalidation lookup, Temporal Legal Context, and existing output schemas.
- [ ] Ensure counter-authority retrieval and strategy alternatives use the same corpus surface, with “not found/unavailable” disclosed rather than invented.
- [ ] Run all relevant layer tests and the prior Week 14 regression suite.

## Task 6: Bilirkişi report production workflow

**Files:** new `legalai/packages/bilirkişi/` (ASCII-safe package name if required by tooling), intake/extraction/technical reasoning modules, MCP server/catalog, focused tests.

- [ ] Write failing tests for text/file intake, supported PDF/DOCX/XLSX/TXT/HTML/image metadata, size/type validation, local PII masking before any external call, and deterministic section/claim extraction.
- [ ] Implement local extraction with optional OCR boundary, technical-domain issue matrix, opposing technical hypotheses, legal-grounding links, temporal-context fields, and per-report-claim objection records.
- [ ] Implement structured analysis and petition-draft builders; outputs must distinguish technical inference, legal inference, cited authority, missing evidence, and non-binding assessment.
- [ ] Expose `socratlegal_bilirkisi_raporu_analiz` and `socratlegal_bilirkisi_raporu_dilekce` plus legacy aliases. Keep prompt resources as guidance, but make production tools active and testable.
- [ ] Run bilirkişi tests and MCP schema tests.

## Task 7: Discovery UX, documentation, and acceptance verification

**Files:** capability docs, IDE/CLI setup docs, `.env.example`, acceptance tests.

- [ ] Write failing acceptance tests for capability discovery, tool selection guidance, source-health reporting, and installation examples for Cursor, Codex, Claude, Antigravity, VS Code, and CLI stdio.
- [ ] Update public documentation to explain the no-hosting model: each user runs a local server, uses configured API/subscription credentials in their client, and optionally syncs selected corpus collections locally.
- [ ] Document local DB size controls, sync freshness, legal-source citations, uncertainty/non-binding disclaimers, and manual Cursor rename steps without touching the user-local config.
- [ ] Run `uv run pytest -q` and record the result; inspect `git diff` to ensure only intended tracked files changed.

## Task 8: Review and handoff

- [ ] Perform a focused code review for upstream compatibility, concurrency, PII handling, secret leakage, and source-authority semantics.
- [ ] If tests pass, present the user with the commit scope and offer the next explicit GitHub push/merge step; do not push without the user’s approval.

