# SocratLegal Portable and Manual Setup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a hosting-free SocratLegal setup that supports a portable archive with no system Python/uv requirement and continues to support safe, fully documented manual JSON/TOML MCP registration.

**Architecture:** Add a small installer domain under `legalai/packages/installer` that resolves platform paths, detects supported IDE configuration files, and performs idempotent JSON/TOML merges. Portable launch scripts invoke the bundled platform `uv` against the packaged project; manual users continue to point an IDE at their local Python/uv checkout. Existing upstream modules and their public contracts remain untouched.

**Tech Stack:** Python 3.11+ for the development checkout, `pathlib`, `json`, `tomllib`/`tomlkit`, Typer, PowerShell, POSIX shell, GitHub Actions, and the existing `uv.lock` dependency workflow.

## Implementation status

Tasks 1–8 are implemented in the local branch. This includes launch models,
safe JSON/TOML merging and repair, IDE discovery and one-command installation,
portable launch/package scripts, release workflow, checksum-verified update and
rollback, user documentation, and the full regression/end-to-end test pass.

## Global Constraints

- No hosting or remote SocratLegal runtime is introduced.
- The portable package must not require system Python, system `uv`, Git, or GitHub CLI.
- Manual JSON/TOML installation remains supported and documented.
- Installer writes one valid root configuration object and never appends a second independent JSON document.
- Existing MCP registrations are preserved; SocratLegal registration is idempotent.
- Installer changes are limited to SocratLegal setup code, scripts, workflows, and documentation; upstream module contracts and source files are not modified.
- Portable runtime data and corpus remain local and are not committed to Git.
- API keys and personal data must not be written to installer logs.
- Executable packaging is explicitly deferred.
- Portable updates use a stable launcher, explicit version metadata, checksum verification, backup, and rollback; the updater is opt-in and never silently overwrites the active application.

---

### Task 1: Define installer models and platform path resolution

**Files:**
- Create: `legalai/packages/installer/__init__.py`
- Create: `legalai/packages/installer/models.py`
- Create: `legalai/packages/installer/paths.py`
- Test: `legalai/tests/installer/test_paths.py`

**Interfaces:**
- `McpLaunchSpec(name: str, command: str, args: tuple[str, ...], cwd: str, env: dict[str, str] | None = None)` is the common launch record.
- `InstallRequest(install_dir: Path, data_dir: Path | None, ide_ids: tuple[str, ...], portable_root: Path | None, dry_run: bool = False, repair: bool = False)` is the installer input.
- `InstallResult(ide_id: str, config_path: Path, status: str, backup_path: Path | None, message: str)` is one IDE result.
- `resolve_data_dir(install_dir: Path, explicit: Path | None) -> Path` uses the explicit path when present and otherwise returns `install_dir / "data"`.
- `build_checkout_launch_spec(project_dir: Path) -> McpLaunchSpec` returns the direct Python module launch used by manual local checkouts.
- `build_portable_launch_spec(portable_root: Path) -> McpLaunchSpec` returns the bundled `runtime/uv` launch used by portable packages.

- [ ] **Step 1: Write failing path and launch tests**

```python
from pathlib import Path

from legalai.packages.installer.paths import (
    build_checkout_launch_spec,
    build_portable_launch_spec,
    resolve_data_dir,
)


def test_explicit_data_directory_wins() -> None:
    assert resolve_data_dir(Path("C:/SocratLegal"), Path("D:/SocratData")) == Path("D:/SocratData")


def test_checkout_launch_uses_module_server() -> None:
    spec = build_checkout_launch_spec(Path("C:/SocratLegal"))
    assert spec.command.endswith(".venv/Scripts/python.exe") or spec.command.endswith(".venv/bin/python")
    assert spec.args == ("-m", "legalai.apps.mcp.server")
    assert spec.cwd == str(Path("C:/SocratLegal"))


def test_portable_launch_uses_bundled_uv() -> None:
    spec = build_portable_launch_spec(Path("C:/SocratLegal"))
    assert spec.command.endswith("runtime/uv.exe") or spec.command.endswith("runtime/uv")
    assert "socratlegal-mcp" in spec.args
    assert spec.cwd.endswith("app")
```

- [ ] **Step 2: Run the focused tests and verify they fail**

Run:

```powershell
uv run pytest legalai/tests/installer/test_paths.py -q
```

Expected: collection failure because the installer package and functions do not yet exist.

- [ ] **Step 3: Implement the models and path functions**

Use `Path` throughout. Select the executable by `os.name`: `.venv/Scripts/python.exe` on Windows and `.venv/bin/python` elsewhere; select `runtime/uv.exe` on Windows and `runtime/uv` elsewhere. The portable arguments must be exactly `("run", "--directory", str(portable_root / "app"), "socratlegal-mcp")` and the working directory must be `portable_root / "app"`.

- [ ] **Step 4: Run the focused tests and verify they pass**

Run:

```powershell
uv run pytest legalai/tests/installer/test_paths.py -q
```

Expected: all path and launch tests pass.

- [ ] **Step 5: Commit the isolated installer model**

```powershell
git add legalai/packages/installer legalai/tests/installer/test_paths.py
git commit -m "feat: add SocratLegal installer launch models"
```

### Task 2: Implement safe JSON/TOML configuration merging

**Files:**
- Create: `legalai/packages/installer/config_merge.py`
- Test: `legalai/tests/installer/test_config_merge.py`
- Modify: `pyproject.toml` to add `tomlkit>=0.13.2`

**Interfaces:**
- `merge_json_config(path: Path, server: McpLaunchSpec, backup_dir: Path | None = None, repair: bool = False) -> InstallResult` writes under `mcpServers.socratlegal`.
- `merge_vscode_json_config(path: Path, server: McpLaunchSpec, backup_dir: Path | None = None, repair: bool = False) -> InstallResult` writes under `servers.socratlegal` with `type: "stdio"`.
- `merge_codex_toml_config(path: Path, server: McpLaunchSpec, backup_dir: Path | None = None) -> InstallResult` writes `[mcp_servers.socratlegal]`.
- `backup_before_write(path: Path, backup_dir: Path | None) -> Path | None` creates a timestamped copy before mutation.
- Every merge is idempotent: running it twice leaves one `socratlegal` entry and preserves unrelated entries.

- [ ] **Step 1: Write failing merge tests**

Cover these exact cases:

```python
import json
from pathlib import Path

import pytest

from legalai.packages.installer.config_merge import (
    merge_codex_toml_config,
    merge_json_config,
    merge_vscode_json_config,
)
from legalai.packages.installer.models import McpLaunchSpec


def server() -> McpLaunchSpec:
    return McpLaunchSpec(
        name="socratlegal",
        command=r"C:\SocratLegal\runtime\uv.exe",
        args=("run", "--directory", r"C:\SocratLegal\app", "socratlegal-mcp"),
        cwd=r"C:\SocratLegal\app",
    )


def test_cursor_merge_preserves_existing_servers(tmp_path: Path) -> None:
    path = tmp_path / "mcp.json"
    path.write_text(json.dumps({"mcpServers": {"other": {"command": "node"}}}), encoding="utf-8")
    result = merge_json_config(path, server())
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert result.status == "installed"
    assert set(payload["mcpServers"]) == {"other", "socratlegal"}


def test_cursor_merge_is_idempotent(tmp_path: Path) -> None:
    path = tmp_path / "mcp.json"
    path.write_text("{\"mcpServers\": {}}", encoding="utf-8")
    merge_json_config(path, server())
    merge_json_config(path, server())
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert list(payload["mcpServers"]).count("socratlegal") == 1


def test_vscode_merge_emits_stdio_type(tmp_path: Path) -> None:
    path = tmp_path / "mcp.json"
    path.write_text("{}", encoding="utf-8")
    merge_vscode_json_config(path, server())
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["servers"]["socratlegal"]["type"] == "stdio"


def test_codex_merge_preserves_other_sections(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text("[features]\nexperimental = true\n", encoding="utf-8")
    merge_codex_toml_config(path, server())
    text = path.read_text(encoding="utf-8")
    assert "experimental = true" in text
    assert "[mcp_servers.socratlegal]" in text


def test_concatenated_json_objects_are_repaired_only_with_repair_flag(tmp_path: Path) -> None:
    path = tmp_path / "mcp.json"
    path.write_text('{"mcpServers": {"one": {}}}\n{"mcpServers": {"two": {}}}', encoding="utf-8")
    refused = merge_json_config(path, server(), repair=False)
    assert refused.status == "invalid"
    repaired = merge_json_config(path, server(), repair=True)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert repaired.status == "installed"
    assert set(payload["mcpServers"]) == {"one", "two", "socratlegal"}


def test_invalid_json_is_not_overwritten_and_backup_is_reported(tmp_path: Path) -> None:
    path = tmp_path / "mcp.json"
    original = '{"mcpServers": '
    path.write_text(original, encoding="utf-8")
    result = merge_json_config(path, server())
    assert result.status == "invalid"
    assert path.read_text(encoding="utf-8") == original


def test_windows_paths_round_trip_without_escape_loss(tmp_path: Path) -> None:
    path = tmp_path / "mcp.json"
    path.write_text("{}", encoding="utf-8")
    merge_json_config(path, server())
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["mcpServers"]["socratlegal"]["cwd"] == r"C:\SocratLegal\app"
```

The concatenated JSON fixture must reproduce the user-facing failure: one valid object followed by a second valid object. With `repair=True`, both `mcpServers` maps are merged into one document; with `repair=False`, no write occurs.

- [ ] **Step 2: Run the focused merge tests and verify they fail**

Run:

```powershell
uv run pytest legalai/tests/installer/test_config_merge.py -q
```

Expected: import or assertion failures because the merge functions are not implemented.

- [ ] **Step 3: Implement JSON parsing, repair, backup, and idempotent merge**

Use `json.loads` for normal files. For repair mode, use `json.JSONDecoder().raw_decode` twice, require only whitespace between roots, require each root to be an object, and merge top-level maps without overwriting unrelated keys. If both roots contain `mcpServers`, merge their child maps. Do not attempt to repair arbitrary malformed JSON.

Use `json.dumps(payload, ensure_ascii=False, indent=2) + "\n"` and write via a temporary sibling file followed by `Path.replace` so a failed write does not truncate the original.

- [ ] **Step 4: Implement VS Code and Codex serializers**

VS Code output must be:

```json
{
  "servers": {
    "socratlegal": {
      "type": "stdio",
      "command": "C:\\SocratLegal\\runtime\\uv.exe",
      "args": ["run", "--directory", "C:\\SocratLegal\\app", "socratlegal-mcp"],
      "cwd": "C:\\SocratLegal\\app"
    }
  }
}
```

Codex output must use a TOML table with `command`, `args`, and `cwd`, preserving unrelated tables. Use `tomlkit` to retain valid TOML formatting and write atomically.

- [ ] **Step 5: Run merge tests and verify they pass**

```powershell
uv run pytest legalai/tests/installer/test_config_merge.py -q
```

Expected: all JSON/TOML preservation, repair, backup, and idempotency tests pass.

- [ ] **Step 6: Commit safe configuration merging**

```powershell
git add pyproject.toml legalai/packages/installer/config_merge.py legalai/tests/installer/test_config_merge.py
git commit -m "feat: add safe SocratLegal MCP config merging"
```

### Task 3: Detect IDEs and expose an installer service

**Files:**
- Create: `legalai/packages/installer/ides.py`
- Create: `legalai/packages/installer/service.py`
- Test: `legalai/tests/installer/test_ide_detection.py`
- Test: `legalai/tests/installer/test_install_service.py`
- Modify: `legalai/apps/cli/main.py`

**Interfaces:**
- `detect_ides(env: Mapping[str, str], home: Path, project_dir: Path | None = None) -> tuple[IdeInstallation, ...]` returns deterministic records for Cursor, Codex, Antigravity, VS Code, and Claude Desktop.
- `install_socratlegal(request: InstallRequest, env: Mapping[str, str] | None = None) -> tuple[InstallResult, ...]` performs selected merges and never mutates an unselected IDE.
- CLI command: `socratlegal install --install-dir PATH --ide cursor --ide codex --portable-root PATH --data-dir PATH --dry-run --repair`.
- `--ide all` expands only to detected IDEs; missing IDEs are reported, not created.

- [ ] **Step 1: Write detection and service tests**

Test known Windows paths using a temporary fake home and environment map. Verify that detection is based on existing files/directories, not on the current process's IDE availability. Test `--dry-run`, selected IDEs, missing IDEs, backup creation, and repeated installation.

- [ ] **Step 2: Run focused tests and verify they fail**

```powershell
uv run pytest legalai/tests/installer/test_ide_detection.py legalai/tests/installer/test_install_service.py -q
```

Expected: import failures because detection and service modules are absent.

- [ ] **Step 3: Implement platform-aware IDE detection**

Use these Windows locations:

- Cursor user config: `%USERPROFILE%\.cursor\mcp.json`.
- Antigravity config: `%USERPROFILE%\.gemini\config\mcp_config.json`.
- VS Code project config: `<project>\.vscode\mcp.json`; do not create it during auto-detection unless the user explicitly selects a project.
- Claude Desktop: `%APPDATA%\Claude\claude_desktop_config.json`.
- Codex project config: `<project>\.codex\config.toml`; user-level Codex config is reported as a manual option when no project is selected.

Use platform home/config conventions for macOS and Linux. Keep the detection layer separate from the serializers so a new IDE does not change existing merge logic.

- [ ] **Step 4: Implement the installer service and CLI command**

The service must:

1. Validate that `install_dir` exists or create it only when the user explicitly requested it.
2. Build a portable launch spec when `portable_root` is given; otherwise build a local checkout spec.
3. Resolve selected IDE configuration paths.
4. Back up and merge each file.
5. Return a structured result for every IDE.
6. Print no API keys, report paths in human-readable form, and return a nonzero CLI exit code if a selected IDE fails.

The CLI must display a plain-language summary such as `SocratLegal Cursor'a eklendi`, `VS Code bulunamadı`, or `JSON geçersiz; dosya değiştirilmedi`.

- [ ] **Step 5: Run detection/service tests and verify they pass**

```powershell
uv run pytest legalai/tests/installer/test_ide_detection.py legalai/tests/installer/test_install_service.py -q
uv run socratlegal install --help
```

Expected: focused tests pass and help lists `--install-dir`, `--ide`, `--portable-root`, `--data-dir`, `--dry-run`, and `--repair`.

- [ ] **Step 6: Commit IDE detection and installer service**

```powershell
git add legalai/apps/cli/main.py legalai/packages/installer legalai/tests/installer/test_ide_detection.py legalai/tests/installer/test_install_service.py
git commit -m "feat: add SocratLegal IDE installer service"
```

### Task 4: Add portable runtime launch scripts

**Files:**
- Create: `scripts/install.ps1`
- Create: `scripts/install.sh`
- Create: `scripts/start.cmd`
- Create: `scripts/start.sh`
- Create: `scripts/portable-manifest.json`
- Test: `legalai/tests/installer/test_portable_layout.py`

**Interfaces:**
- `scripts/start.cmd` invokes `runtime\uv.exe run --directory app socratlegal-mcp`.
- `scripts/start.sh` invokes `runtime/uv run --directory app socratlegal-mcp`.
- `scripts/install.ps1` accepts `-InstallDir`, `-DataDir`, repeated `-Ide`, `-PortableRoot`, `-DryRun`, and `-Repair`.
- `scripts/install.sh` accepts `--install-dir`, `--data-dir`, repeated `--ide`, `--portable-root`, `--dry-run`, and `--repair`.
- `portable-manifest.json` records the package format version, supported platform, runtime filename, and application version; it contains no secrets.

- [ ] **Step 1: Write portable layout tests**

Create a temporary portable root and assert that the manifest, `app`, `runtime`, and launcher paths are validated. Test that a missing runtime produces a clear error before any IDE configuration is changed.

- [ ] **Step 2: Run the layout tests and verify they fail**

```powershell
uv run pytest legalai/tests/installer/test_portable_layout.py -q
```

Expected: failure because portable validation and manifests are absent.

- [ ] **Step 3: Implement launchers and scripts**

The scripts must resolve their own directory rather than rely on the caller's working directory. They must pass `--portable-root` and `--install-dir` to the Python installer command, preserve spaces in Windows paths, and return the child process exit code. They must report that first launch may download locked dependencies, while never requiring a system Python or system `uv`.

- [ ] **Step 4: Run shell syntax and layout tests**

```powershell
uv run pytest legalai/tests/installer/test_portable_layout.py -q
```

On Windows, run the launcher smoke test with a temporary copy and assert that the command reaches the MCP entry point without importing user-global Python. On POSIX CI, run `shellcheck` if available and execute `start.sh --help` through a stub runtime.

- [ ] **Step 5: Commit portable scripts**

```powershell
git add scripts legalai/tests/installer/test_portable_layout.py
git commit -m "feat: add SocratLegal portable launch scripts"
```

### Task 5: Build platform archives in GitHub Actions

**Files:**
- Create: `.github/workflows/portable-release.yml`
- Modify: `scripts/portable-manifest.json`
- Create: `scripts/package_portable.py`
- Test: `legalai/tests/installer/test_package_manifest.py`

**Interfaces:**
- `python scripts/package_portable.py --platform PLATFORM --output DIRECTORY --version VERSION` creates one archive and one checksum file.
- The workflow runs on Windows x64, macOS arm64, macOS x64, and Linux x64 matrices.
- The workflow triggers only on a published GitHub Release or explicit `workflow_dispatch`; it does not alter PyPI publishing behavior.

- [ ] **Step 1: Write manifest and packaging tests**

Test that the archive contains `app/pyproject.toml`, `app/uv.lock`, the platform runtime, both the installer and start launcher, and the manifest. Test that user `.data` directories and `.env` files are excluded.

- [ ] **Step 2: Run packaging tests and verify they fail**

```powershell
uv run pytest legalai/tests/installer/test_package_manifest.py -q
```

Expected: failure because the package builder is absent.

- [ ] **Step 3: Implement deterministic archive creation**

The builder must copy only tracked application files and release scripts, use the pinned runtime filename from the manifest, exclude `.venv`, `.data`, `.env`, PII maps, logs, test caches, and user configuration, and emit a SHA-256 checksum beside the archive.

- [ ] **Step 4: Add the release workflow**

Use a matrix with explicit platform labels, build each archive independently, upload artifacts, and publish them as release assets. The workflow must not require `gh`, must not push source changes, and must fail if the expected runtime binary or checksum is missing.

- [ ] **Step 5: Run packaging tests and verify they pass**

```powershell
uv run pytest legalai/tests/installer/test_package_manifest.py -q
```

Expected: all archive-content and exclusion tests pass.

- [ ] **Step 6: Commit release packaging**

```powershell
git add .github/workflows/portable-release.yml scripts/portable-manifest.json scripts/package_portable.py legalai/tests/installer/test_package_manifest.py
git commit -m "ci: build SocratLegal portable release archives"
```

### Task 6: Add version checking, safe portable updates, and rollback

**Files:**
- Create: `legalai/packages/installer/update.py`
- Create: `legalai/packages/installer/versioning.py`
- Create: `legalai/tests/installer/test_update.py`
- Modify: `scripts/portable-manifest.json`
- Modify: `scripts/start.cmd`
- Modify: `scripts/start.sh`
- Modify: `scripts/install.ps1`
- Modify: `scripts/install.sh`

**Interfaces:**
- `ReleaseManifest(version: str, channel: str, release_url: str, archive_name: str, sha256: str, data_schema_version: int, minimum_supported_version: str)` represents a published release.
- `compare_versions(current: str, available: str) -> int` returns `-1`, `0`, or `1` using PEP 440-compatible versions.
- `check_for_update(current: ReleaseManifest, metadata_url: str, http_get: Callable[[str], bytes]) -> UpdateCheckResult` retrieves only release metadata and never sends document text.
- `apply_update(install_root: Path, archive: Path, expected_sha256: str, backup_root: Path) -> UpdateResult` verifies the archive, stages it, preserves `data`, atomically replaces `app`, and records `app.previous` for rollback.
- `rollback_update(install_root: Path) -> UpdateResult` restores the previous application after a failed startup validation.

- [ ] **Step 1: Write failing version and update tests**

Cover current/equal/newer versions, malformed metadata, checksum mismatch, successful replacement, preservation of `data`, backup creation, and rollback after a failed health marker. Verify that a failed update leaves the active application untouched.

- [ ] **Step 2: Run focused update tests and verify they fail**

```powershell
uv run pytest legalai/tests/installer/test_update.py -q
```

Expected: collection failure because version and update modules are absent.

- [ ] **Step 3: Implement manifest parsing and version comparison**

Use a strict JSON manifest schema. Reject missing version, archive, checksum, channel, or minimum-version fields. Use `packaging.version.Version` already available through the project dependency graph; if it is not directly available, add `packaging>=24.0` explicitly rather than comparing version strings lexicographically.

- [ ] **Step 4: Implement metadata-only update checking**

The checker must be opt-in, rate-limited to one check per 24 hours by a local timestamp, and return `available`, `current_version`, `available_version`, and `message`. Network failure must degrade to `status = unavailable` without affecting MCP startup.

- [ ] **Step 5: Implement staged update, checksum verification, backup, and rollback**

Download/extract into a temporary sibling directory. Verify SHA-256 before touching the active app. Rename the active `app` to `app.previous`, move the staged `app` into place, preserve `data`, and write an update marker. If the post-update startup validation fails, restore `app.previous` and remove the incomplete app. Never replace IDE configuration files as part of an app update.

- [ ] **Step 6: Route launch scripts through the stable update-aware launcher**

The launchers must continue to start the active `app` path regardless of version. They may print an available-update notice, but they must not auto-apply an update without explicit `--apply-update` or installer confirmation. A failed metadata check must not prevent the current server from starting.

- [ ] **Step 7: Run update tests and verify they pass**

```powershell
uv run pytest legalai/tests/installer/test_update.py -q
```

Expected: all version, checksum, preservation, backup, and rollback tests pass.

- [ ] **Step 8: Commit the safe update lifecycle**

```powershell
git add legalai/packages/installer/update.py legalai/packages/installer/versioning.py legalai/tests/installer/test_update.py scripts/portable-manifest.json scripts/start.cmd scripts/start.sh scripts/install.ps1 scripts/install.sh
git commit -m "feat: add safe SocratLegal portable updates"
```

### Task 7: Rewrite user-facing README and setup documentation

**Files:**
- Modify: `README.md`
- Modify: `docs/socratlegal-setup.md`
- Modify: `docs/mcp-client-setup.md`
- Create: `docs/socratlegal-user-install.md`
- Test: `legalai/tests/apps/test_installation_docs.py`

**Interfaces:**
- Documentation must present portable setup first and manual setup second.
- The manual section must use the variable `SOCRATLEGAL_DIR` in examples and show how a Windows user substitutes the real folder path.
- The docs must explicitly say not to paste the GitHub repository URL into a remote MCP URL field.
- The docs must contain the exact post-install checks `socratlegal_saglik_kontrolu` and `socratlegal_yardim`.

- [ ] **Step 1: Write documentation acceptance tests**

Assert that the documentation contains `Portable`, `Manual JSON`, `Cursor`, `Codex`, `Antigravity`, `VS Code`, `Claude`, `socratlegal_saglik_kontrolu`, the single-root-JSON warning, and the no-hosting explanation. Assert that old text describing bilirkişi production tools as merely planned is absent from public setup docs.

- [ ] **Step 2: Run documentation tests and verify they fail**

```powershell
uv run pytest legalai/tests/apps/test_installation_docs.py -q
```

Expected: failures because the current README and setup documents use old LegalAI/manual-only wording.

- [ ] **Step 3: Write the portable-first user guide**

Explain the workflow in nontechnical language: download the platform archive, extract it, run the installer, select IDEs, restart the IDE, run health check. Explain that GitHub is only the download channel and that SocratLegal still runs locally.

- [ ] **Step 4: Write the manual JSON/TOML guide**

Provide complete examples for the local checkout and portable launch modes. Show the `mcpServers` versus VS Code `servers` difference, the Codex TOML section, Windows double backslashes, path replacement, backup advice, and JSON validation with `ConvertFrom-Json`.

- [ ] **Step 5: Remove stale public installation claims**

Update branding to SocratLegal where public-facing, retain legacy tool aliases where technically necessary, and state that bilirkişi production tools are active but the deep technical-research enhancement is a separate development phase.

- [ ] **Step 6: Run documentation tests**

```powershell
uv run pytest legalai/tests/apps/test_installation_docs.py -q
```

Expected: all documentation assertions pass.

- [ ] **Step 7: Commit user-facing setup documentation**

```powershell
git add README.md docs/socratlegal-setup.md docs/mcp-client-setup.md docs/socratlegal-user-install.md legalai/tests/apps/test_installation_docs.py
git commit -m "docs: add portable-first SocratLegal installation guide"
```

### Task 8: End-to-end verification and handoff

**Files:**
- Test: `legalai/tests/installer/test_end_to_end_install.py`
- Modify: no production files unless a verification failure identifies a scoped defect.

- [ ] **Step 1: Test clean configuration installation**

Use temporary Cursor, Antigravity, VS Code, Claude, and Codex configuration files. Run the service twice and verify one `socratlegal` registration per client, preserved unrelated registrations, and timestamped backups.

- [ ] **Step 2: Test the user’s concatenated JSON failure mode**

Feed the two-root JSON shape shown in the Cursor/Antigravity screenshots. Verify that normal mode refuses to overwrite it, repair mode creates a backup and produces one valid merged root, and the resulting document passes a second parse.

- [ ] **Step 3: Test portable MCP discovery**

Run the portable launch spec through a stub runtime and then the real local runtime. Verify `tools/list` includes `socratlegal_katmanli_analiz`, `socratlegal_agresif_karsi_taraf`, `socratlegal_derin_arastirma`, and both bilirkişi tools.

- [ ] **Step 4: Run the full regression suite**

```powershell
uv run pytest -q
```

Expected: all existing upstream and LegalAI tests pass; no upstream module file is modified.

- [ ] **Step 5: Inspect the final diff and status**

```powershell
git diff --check
git status --short
git diff --stat origin/feature/hafta10-tenant-usage...HEAD
```

Expected: only installer, packaging, workflow, documentation, and tests from this plan are included; existing user changes such as `.cursor/mcp.json` and `.superpowers/` are not staged.

- [ ] **Step 6: Present the user with push options**

Report the test result and offer:

1. Push the commits to the feature branch for the user to merge.
2. Keep the commits local for another review cycle.

Do not push until the user explicitly chooses the first option.
