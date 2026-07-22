# Portable One-Click Update Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task with verification checkpoints.

**Goal:** Add a Windows portable `update.cmd` flow that fetches a release manifest, asks for consent, downloads and verifies the release archive, and updates only the application layer.

**Architecture:** Keep `update.cmd` as a thin packaged launcher. Put HTTPS validation, streaming download, archive-name/checksum verification, and application replacement in `legalai/packages/installer/update.py`; expose the prompt and readable output through `legalai/apps/cli/main.py`. Reuse `apply_update` so `config`, `data`, API keys, documents, and corpus remain outside the replaced `app` directory.

**Tech Stack:** Python 3.11+, Typer, `urllib.request`, existing ZIP/TAR extraction and SHA-256 code, PowerShell/CMD launchers, pytest.

## Global Constraints

- Windows x64 portable release with bundled `runtime\\uv.exe`.
- Manifest and archive URLs must use HTTPS.
- No active application replacement before filename and SHA-256 verification.
- Explicit user confirmation is required by default; no silent background installation.
- `config`, `data`, `.env`, documents, and local corpus are preserved.
- Existing `apply_update` and `rollback_update` behavior remains compatible.
- Branch and tag names contain ASCII characters only.

---

### Task 1: Define failing downloader, CLI, and launcher tests

**Files:**
- Modify: `legalai/tests/installer/test_update.py`
- Modify: `legalai/tests/installer/test_portable_layout.py`

**Interfaces:**
- `download_release_archive(manifest, destination, get=...) -> Path`.
- `socratlegal update install --manifest-file ... --active-app ... --yes`.
- `scripts/update.cmd` exists and invokes the bundled runtime.

- [ ] Write a downloader test with a valid manifest and injected byte-returning `get`; assert the destination contains the bytes.
- [ ] Write a downloader error test; injected `OSError` must become `UpdateError` with `Arşiv indirilemedi`.
- [ ] Write a CLI success test using a local manifest and `--yes`; assert the new app file and `app.previous` old file.
- [ ] Write a CLI cancellation test; invoke without `--yes`, answer `n`, and assert the active app is unchanged.
- [ ] Extend the portable layout test to require `scripts/update.cmd`, `runtime\\uv.exe`, `update install`, `--active-app`, and `windows-x64`.
- [ ] Run the focused tests and verify RED:

```powershell
uv run --no-sync pytest legalai/tests/installer/test_update.py legalai/tests/installer/test_portable_layout.py -q
```

Expected: failures because the downloader, CLI command, and launcher are not implemented.
- [ ] Commit: `git add legalai/tests/installer/test_update.py legalai/tests/installer/test_portable_layout.py; git commit -m "test: define portable one-click update contracts"`

### Task 2: Implement secure archive download and CLI install command

**Files:**
- Modify: `legalai/packages/installer/update.py`
- Modify: `legalai/apps/cli/main.py`
- Test: `legalai/tests/installer/test_update.py`

**Interfaces:**
- `download_release_archive(manifest: ReleaseManifest, destination: Path, *, get: Callable[[str], bytes] | None = None) -> Path`.
- CLI options: `--manifest-file` or `--manifest-url`, `--platform-tag`, `--active-app`, `--current-version`, and `--yes`.

- [ ] Add `download_release_archive` after `archive_download_url`. Derive the asset URL, require HTTPS, write the response to the destination, reject empty content, and wrap `OSError`, `URLError`, `TypeError`, and `ValueError` as `UpdateError("Arşiv indirilemedi: ...")`. Production uses `urlopen(url, timeout=60)`; tests use the injected `get`.
- [ ] Run `uv run --no-sync pytest legalai/tests/installer/test_update.py -q`; downloader tests must pass before the CLI implementation.
- [ ] Add `update install`: load a local manifest or fetch a fresh HTTPS manifest, compare versions, return without downloading when current, prompt with `typer.confirm` unless `--yes`, create a temporary archive beside `active_app`, call `apply_update`, and remove the temporary file in `finally`.
- [ ] Convert update errors to readable `typer.BadParameter` output and print the installed version.
- [ ] Run the update tests again; all update tests must pass.
- [ ] Commit: `git add legalai/packages/installer/update.py legalai/apps/cli/main.py legalai/tests/installer/test_update.py; git commit -m "feat: add checksum-verified portable update install"`

### Task 3: Add packaged Windows launcher and packaging coverage

**Files:**
- Create: `scripts/update.cmd`
- Modify: `scripts/package_portable.py`
- Modify: `legalai/tests/installer/test_portable_layout.py`
- Modify: `legalai/tests/installer/test_packaging.py`

- [ ] Create `scripts/update.cmd` using the existing root-detection pattern:

```bat
@echo off
setlocal
set "HERE=%~dp0"
if exist "%HERE%app" (set "ROOT=%HERE%") else (set "ROOT=%HERE%..")
set "SOCRATLEGAL_ENV_FILE=%ROOT%config\.env"
"%ROOT%\runtime\uv.exe" run --directory "%ROOT%\app" socratlegal update install --active-app "%ROOT%\app" --platform-tag windows-x64
set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" pause
exit /b %EXIT_CODE%
```

- [ ] Add `update.cmd` to `ROOT_ASSETS`.
- [ ] Assert the launcher is included in a built archive and `.env`, `data`, `tmp`, and cache folders remain excluded.
- [ ] Run `uv run --no-sync pytest legalai/tests/installer/test_portable_layout.py legalai/tests/installer/test_packaging.py -q`.
- [ ] Commit: `git add scripts/update.cmd scripts/package_portable.py legalai/tests/installer/test_portable_layout.py legalai/tests/installer/test_packaging.py; git commit -m "feat: add portable update cmd launcher"`

### Task 4: Document the safe one-click flow

**Files:**
- Modify: `docs/socratlegal-user-install.md`
- Modify: `README.md` only if the release entry point needs a link
- Modify: `legalai/tests/installer/test_docs.py`

- [ ] Add failing assertions requiring `update.cmd`, explicit consent, checksum verification, preservation of `config/data`, and the absence of silent installation.
- [ ] Run `uv run --no-sync pytest legalai/tests/installer/test_docs.py -q` and verify RED.
- [ ] Document: close IDEs, double-click `update.cmd`, approve, wait for verification, restart IDEs. Keep the manual `update check/apply/rollback` path for advanced users.
- [ ] Run the docs tests and commit: `git add docs/socratlegal-user-install.md README.md legalai/tests/installer/test_docs.py; git commit -m "docs: explain one-click portable updates"`

### Task 5: Verify v0.2.5 release candidate

**Files:**
- Verify: `.github/workflows/portable-release.yml`
- Verify: `legalai/tests/installer`, `legalai/tests/apps`, and the full pytest suite

- [ ] Run `uv run --no-sync pytest legalai/tests/installer legalai/tests/apps -q`.
- [ ] Run the full suite with worktree-local `TEMP`, `TMP`, `UV_CACHE_DIR`, and `PYTHONPATH`; expected result is no failures.
- [ ] Build the local Windows x64 candidate and verify it contains `update.cmd`, `install.ps1`, `start.cmd`, and `runtime/uv.exe`, but no `.env`, `data`, `tmp`, or cache folders.
- [ ] Run `git diff --check` and `git status --short --branch`; remove only generated temporary folders before handoff.
- [ ] Do not push or tag until all checks pass and the branch is clean.
