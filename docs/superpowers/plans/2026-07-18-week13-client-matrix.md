# Week 13 Çoklu İstemci Uyumluluğu Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Codex, Cursor, Claude, Antigravity ve VS Code için ortak yerel STDIO MCP akışını config dosyalarına dokunmadan doğrulamak ve kullanıcı rehberini tamamlamak.

**Architecture:** Testler yalnızca mevcut Codex TOML ve Cursor JSON kayıtlarını okur; üretim kodu istemciye özel dallanma içermez. Yeni istemci matrisi, aynı portable `uv run legalai-mcp` akışını ve ortak health/discovery adımlarını açıklar.

**Tech Stack:** Python 3.11+, `tomllib`, `json`, pytest, mevcut FastMCP server.

## Global Constraints

- `.codex/config.toml` ve `.cursor/mcp.json` değiştirilmeyecek.
- Cursor'daki `yargi-mcp-fork` kaydı korunacak.
- Config smoke testleri dosya yazmayacak.
- Secret, API key ve kullanıcıya özel yeni mutlak yol eklenmeyecek.
- Hosting veya ortak port eklenmeyecek.
- Week 14 persona promptları bu planın kapsamında değil.

### Task 1: Config-independent client smoke tests

**Files:**
- Create: `legalai/tests/apps/test_mcp_client_matrix.py`

- [ ] **Step 1: Write failing tests** for TOML/JSON parsing, `legalai` STDIO records, Cursor upstream entry preservation, and secret-free config text.
- [ ] **Step 2: Run:** `uv run --no-cache pytest legalai/tests/apps/test_mcp_client_matrix.py -q` and confirm the new matrix test fails for the missing expected client matrix contract.
- [ ] **Step 3: Implement only the test helper assertions** using `tomllib` and `json`; do not modify config files or production code.
- [ ] **Step 4: Run focused test and expect pass.**
- [ ] **Step 5: Commit:** `test: verify multi-client mcp configuration compatibility`.

### Task 2: Portable client matrix documentation

**Files:**
- Create: `docs/mcp-client-matrix.md`
- Modify: `docs/mcp-client-setup.md` only to link the matrix.

- [ ] **Step 1: Add documentation test markers** to the matrix test for all five clients, `uv run legalai-mcp`, health-check, discovery, resource URI, and no-config-overwrite guidance.
- [ ] **Step 2: Run focused test and confirm red for missing document.**
- [ ] **Step 3: Write the matrix with portable snippets, IDE-specific equivalent menu names, first-run sequence, troubleshooting, and the distinction between host subscription and optional server API keys.**
- [ ] **Step 4: Run focused test and expect pass.**
- [ ] **Step 5: Commit:** `docs: add multi-client mcp usage matrix`.

### Task 3: Final verification

- [ ] Run targeted app/config tests.
- [ ] Run `.venv\Scripts\python.exe -m pytest -q`.
- [ ] Run `uv run --no-cache pytest -q`.
- [ ] Run MCP health/discovery/resource/prompt smoke test.
- [ ] Run `git diff --check` and verify only intended files are staged.
- [ ] Record exact counts and offer Cursor push/merge checkpoint.

## Execution status

- [x] Task 1: config smoke tests — focused suite `3 passed`; Codex TOML and Cursor JSON remained unchanged.
- [x] Task 2: client matrix documentation — commit `396bae3`; five-client matrix and first-run flow added.
- [x] Task 3: final verification — targeted MCP/config suite `9 passed`; `.venv` full suite `172 passed`; `uv run` full suite `172 passed`; health/discovery/resource smoke successful.
