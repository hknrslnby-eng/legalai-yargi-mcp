# v0.2.5 Release Version and Installer Matrix Implementation Plan

> For agentic workers: use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax.

Goal: Publish v0.2.5 with one consistent runtime/package/tag version and automated validation for all five supported IDE configuration formats.

Architecture: legalai.__version__ is the single application version source. Setuptools reads it dynamically; MCP, API, and CLI import it. A release validator compares the tag with the source version, while temporary-directory tests validate Cursor, Antigravity, VS Code, Claude Desktop, and Codex without touching user settings.

Tech Stack: Python 3.11+, setuptools, uv, pytest, JSON/TOML merge helpers, GitHub Actions, PowerShell.

## Global Constraints

- Base changes on merged origin/main commit 3319859.
- Work only in C:/Users/hakan/Desktop/Yargi MCP Fork/legalai-yargi-mcp/.worktrees/release-version-installer-matrix.
- Use ASCII branch fix/release-version-and-installer-matrix.
- Target version is exactly 0.2.5.
- Do not force-rewrite v0.2.4.
- Do not touch the user's Cursor or Antigravity files.
- Produce Windows x64 portable assets only.
- Never package API keys, .env, corpus data, logs, or IDE state.

---

### Task 1: Define failing version and release-validator tests

Files:
- Create legalai/tests/test_version_contract.py
- Create legalai/tests/test_release_version.py
- Later create scripts/check_release_version.py

- [ ] Step 1: Write the failing runtime contract.

    from importlib.metadata import version

    from legalai import __version__
    from legalai.apps.api.app import app as api_app
    from legalai.apps.mcp.server import app as mcp_app

    def test_runtime_surfaces_report_package_version() -> None:
        package_version = version("yargi-mcp")
        assert package_version == "0.2.5"
        assert __version__ == package_version
        assert api_app.version == package_version
        assert mcp_app.version == package_version

- [ ] Step 2: Verify RED.

Run: uv run pytest legalai/tests/test_version_contract.py -q

Expected: failure because the current source reports an older version.

- [ ] Step 3: Write the failing release-validator contract.

    import pytest
    from scripts.check_release_version import ReleaseVersionError, check_release_version

    def test_validator_accepts_matching_tag() -> None:
        check_release_version("v0.2.5", "0.2.5")

    def test_validator_rejects_mismatch() -> None:
        with pytest.raises(ReleaseVersionError):
            check_release_version("v0.2.4", "0.2.5")

- [ ] Step 4: Verify RED.

Run: uv run pytest legalai/tests/test_release_version.py -q

Expected: collection failure because the validator does not yet exist.

- [ ] Step 5: Commit the red tests.

    git add legalai/tests/test_version_contract.py legalai/tests/test_release_version.py
    git commit -m "test: define v0.2.5 version contracts"

---

### Task 2: Centralize the runtime/package version

Files:
- Modify pyproject.toml
- Modify legalai/__init__.py
- Modify legalai/apps/mcp/server.py
- Modify legalai/apps/api/app.py
- Modify legalai/apps/cli/main.py
- Test legalai/tests/test_version_contract.py

- [ ] Step 1: Set the only manually maintained version.

Set legalai/__init__.py to:

    __version__ = "0.2.5"

- [ ] Step 2: Make setuptools read that value.

Replace the static project version in pyproject.toml with:

    [project]
    name = "yargi-mcp"
    dynamic = ["version"]

Add:

    [tool.setuptools.dynamic]
    version = {attr = "legalai.__version__"}

Keep all other project metadata unchanged.

- [ ] Step 3: Remove runtime version literals.

Import __version__ from legalai in the MCP server, API app, and CLI. Use it for FastMCP, FastAPI, CLI --current-version, and every update-check default.

- [ ] Step 4: Verify GREEN.

Run: uv run pytest legalai/tests/test_version_contract.py -q

Expected: PASS.

- [ ] Step 5: Scan for stale current values.

Run:

    git grep -n "0\.2\.3" -- pyproject.toml legalai scripts .github README.md docs

Classify any remaining historical example; current runtime and release references must contain no stale value.

- [ ] Step 6: Commit.

    git add pyproject.toml legalai/__init__.py legalai/apps/mcp/server.py legalai/apps/api/app.py legalai/apps/cli/main.py legalai/tests/test_version_contract.py
    git commit -m "fix: centralize v0.2.5 runtime version"

---

### Task 3: Add and enforce release tag validation

Files:
- Create scripts/check_release_version.py
- Modify .github/workflows/portable-release.yml
- Test legalai/tests/test_release_version.py

- [ ] Step 1: Implement the minimal validator.

Implement check_release_version(tag: str, source_version: str) -> None, ReleaseVersionError, and a CLI accepting one tag. Strip one leading v; reject empty or malformed values and mismatches with exit code 1; print a success line on match.

- [ ] Step 2: Verify GREEN.

Run: uv run pytest legalai/tests/test_release_version.py -q

Expected: PASS.

- [ ] Step 3: Add the workflow guard before packaging.

    - name: Verify release version
      shell: bash
      run: python scripts/check_release_version.py "${GITHUB_REF_NAME}"

The guard must run before package_portable.py.

- [ ] Step 4: Verify the CLI.

uv run python scripts/check_release_version.py v0.2.5 must exit 0.
uv run python scripts/check_release_version.py v0.2.4 must exit non-zero.

- [ ] Step 5: Commit.

    git add scripts/check_release_version.py legalai/tests/test_release_version.py .github/workflows/portable-release.yml
    git commit -m "ci: reject release tag version mismatches"

---

### Task 4: Cover all supported IDE installers

Files:
- Modify legalai/tests/installer/test_service.py
- Modify legalai/tests/installer/test_config_merge.py only if a missing schema assertion is discovered

- [ ] Step 1: Add a temporary-directory five-IDE test.

Use tmp_path for home, appdata, project, and install directory. Install cursor, antigravity, vscode, claude, and codex. Assert that all five result IDs are present, Cursor has a socratlegal mcpServers entry, Codex has a mcp_servers.socratlegal table, and VS Code has a servers.socratlegal entry with type stdio.

Seed unrelated Cursor/Codex servers and assert they remain. Run installation twice and assert the second result for every IDE is unchanged.

- [ ] Step 2: Verify RED or confirm existing behavior.

Run: uv run pytest legalai/tests/installer/test_service.py -q

If it fails, record the expected assertion and make only the minimum production change. If it passes immediately, retain it as regression coverage and do not alter installer behavior.

- [ ] Step 3: Run the full installer matrix.

Run: uv run pytest legalai/tests/installer legalai/tests/apps -q

Expected: PASS with zero failures.

- [ ] Step 4: Commit.

    git add legalai/tests/installer/test_service.py legalai/tests/installer/test_config_merge.py
    git commit -m "test: cover all supported IDE installer formats"

---

### Task 5: Make the release workflow test before uploading

Files:
- Modify .github/workflows/portable-release.yml
- Modify legalai/tests/installer/test_packaging.py only if required
- Modify legalai/tests/installer/test_portable_layout.py only if required

- [ ] Step 1: Add preflight test execution.

After bundled uv is available and before packaging, run:

    runtime-download/uv.exe sync --frozen --dev
    runtime-download/uv.exe run pytest legalai/tests/installer legalai/tests/apps -q

Keep the Windows x64 matrix and existing asset names.

- [ ] Step 2: Assert package/manifest consistency.

Extend packaging tests to assert that the staged application reports 0.2.5, the generated manifest reports the requested archive version, runtime is included, and .env, data, logs, .git, and IDE state are excluded.

- [ ] Step 3: Run locally.

Run: uv run pytest legalai/tests/installer legalai/tests/apps -q

Expected: PASS.

- [ ] Step 4: Commit.

    git add .github/workflows/portable-release.yml legalai/tests/installer/test_packaging.py legalai/tests/installer/test_portable_layout.py
    git commit -m "ci: validate portable package before release"

---

### Task 6: Align current documentation and verify the whole repository

Files:
- Modify README.md current release links/examples
- Modify docs/week11-demo.md current version example only
- Test legalai/tests/installer/test_docs.py

- [ ] Step 1: Update current references to v0.2.5.

Update current release links and user-facing current version examples. Do not rewrite historical statements.

- [ ] Step 2: Verify docs and stale values.

Run:

    uv run pytest legalai/tests/installer/test_docs.py -q
    git grep -n "0\.2\.3" -- pyproject.toml legalai scripts .github README.md docs

Only intentionally historical references may remain.

- [ ] Step 3: Run the complete suite and hygiene checks.

    uv run pytest -q
    git diff --check
    git status --short

Expected: zero test failures, no whitespace errors, and only intended files changed.

- [ ] Step 4: Commit.

    git add README.md docs/week11-demo.md legalai/tests/installer/test_docs.py
    git commit -m "docs: align current release references to v0.2.5"

---

### Task 7: Merge, tag, release, and real-host verification

Files: no source changes expected.

- [ ] Step 1: Verify branch scope.

    git log --oneline origin/main..HEAD
    git diff --stat origin/main...HEAD

- [ ] Step 2: Verify local runtime.

    uv run python -c "from legalai import __version__; from legalai.apps.mcp.server import app; print(__version__); print(app.version)"

Both lines must be 0.2.5.

- [ ] Step 3: Push and open a PR.

    git push -u origin fix/release-version-and-installer-matrix

Open a PR into main and merge only after all checks are green.

- [ ] Step 4: Tag only after merge.

    git fetch origin main --prune
    git tag -a v0.2.5 origin/main -m "SocratLegal v0.2.5"
    git show v0.2.5 --no-patch
    git push origin v0.2.5

- [ ] Step 5: Verify release assets.

Confirm these assets exist:
- socratlegal-0.2.5-windows-x64.zip
- socratlegal-0.2.5-windows-x64.zip.sha256
- release-manifest-windows-x64.json

- [ ] Step 6: Perform real host checks.

Use the v0.2.5 portable ZIP for Codex and a fresh origin/main source worktree for VS Code. Codex must return status ok, version 0.2.5, external_calls false; VS Code must load the source MCP entry from .vscode/mcp.json.
