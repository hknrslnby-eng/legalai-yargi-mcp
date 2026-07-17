# Week 11 Keşif, Demo ve Health-Check Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Yerel IDE/MCP istemcilerinde LegalAI'nin bağlantı kontrolünü, yetenek keşfini ve yalın-yönlendirilmiş-rafine kullanımını anlaşılır hâle getirmek; aynı pipeline için yardımcı bir `legalai qa` CLI yüzeyi sağlamak.

**Architecture:** `legalai_saglik_kontrolu` dış çağrı yapmayan deterministik bir MCP tool olacaktır. `legalai_yardim` ve `legalai://capabilities` mevcut keşif yüzeyleri korunacaktır. `legalai qa` mevcut `run_pipeline(..., synthesize=False)` domain akışını çağıracaktır; yeni analiz mantığı eklenmeyecektir. README, demo ve katkı belgeleri Codex, Cursor, Claude, Antigravity ve VS Code yerel istemcilerini birinci sınıf hedef kabul edecektir.

**Tech Stack:** Python 3.11+, FastMCP, Typer, mevcut `run_pipeline`, pytest/pytest-asyncio, uv.

## Global Constraints

- Ayrı hosting, global daemon veya ortak TCP portu eklenmeyecek.
- Yerel IDE/MCP istemcileri ana kullanıcı akışı; CLI yalnızca yardımcı ve otomasyon kanalıdır.
- Mevcut `.cursor/mcp.json`, `.codex/config.toml`, secretlar ve kullanıcıya özel ayarlar değiştirilmeyecek.
- Her üretim kodu değişikliğinden önce davranışı gösteren failing test yazılacak.
- MCP health-check hiçbir dış API, veritabanı veya LLM çağrısı yapmayacak.
- Hukuki çıktı `analysis_only=true` ve `non_binding=true` sözleşmesini koruyacak.
- Demo metinleri kişisel veri, gerçek dosya veya API anahtarı içermeyecek.
- LegalAI'nin başlattığı dış çağrılarda mevcut outbound PII maskesi korunacak.
- Üretim kodu yalnızca bir görev için sorumlu alt ajan tarafından değiştirilecek; diğer görevlerin değişiklikleri geri alınmayacak.

---

### Task 1: Deterministic MCP health-check

**Files:**
- Modify: `legalai/apps/mcp/server.py`
- Create: `legalai/tests/apps/test_mcp_health.py`

**Interfaces:**
- Registered tool: `legalai_saglik_kontrolu`
- Direct Python facade: `async def legalai_saglik_kontrolu() -> dict[str, object]`
- Return shape: `{"status": "ok", "version": "0.1.0", "external_calls": False}`

- [ ] **Step 1: Write the failing test**

```python
import pytest

import legalai.apps.mcp.server as server_module


@pytest.mark.asyncio
async def test_health_check_is_local_and_reports_version() -> None:
    payload = await server_module.legalai_saglik_kontrolu()

    assert payload["status"] == "ok"
    assert payload["version"] == server_module.app.version
    assert payload["external_calls"] is False
```

- [ ] **Step 2: Run the focused test and confirm the expected missing-function failure**

Run: `uv run --no-cache pytest legalai/tests/apps/test_mcp_health.py -q`

Expected: FAIL because `legalai_saglik_kontrolu` does not yet exist.

- [ ] **Step 3: Implement the minimal MCP tool and facade**

```python
@app.tool(
    name="legalai_saglik_kontrolu",
    description="LegalAI MCP bağlantısını dış API çağırmadan kontrol eder.",
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
async def _legalai_saglik_kontrolu_tool() -> dict[str, object]:
    return {"status": "ok", "version": app.version, "external_calls": False}


async def legalai_saglik_kontrolu() -> dict[str, object]:
    return await _legalai_saglik_kontrolu_tool.fn()
```

- [ ] **Step 4: Run focused test and verify pass**

Run: `uv run --no-cache pytest legalai/tests/apps/test_mcp_health.py -q`

Expected: `1 passed`.

- [ ] **Step 5: Commit**

```powershell
git add legalai/apps/mcp/server.py legalai/tests/apps/test_mcp_health.py
git commit -m "feat: add local mcp health check"
```

### Task 2: `legalai qa` helper CLI

**Files:**
- Modify: `legalai/apps/cli/main.py`
- Create: `legalai/tests/cli/test_qa_cli.py`

**Interfaces:**
- Command: `legalai qa "Soru" [--mode layered] [--jurisdiction-hint hukuk]`
- Default: `mode="layered"`, `synthesize=False`
- Output: `run_pipeline(...).to_dict()` serialized as UTF-8 JSON.
- Accepted modes: `layered`, `simple`.

- [ ] **Step 1: Write the failing tests**

```python
import json

from typer.testing import CliRunner

import legalai.apps.cli.main as cli_module


class _FakeResult:
    def to_dict(self):
        return {"question": "soru", "analysis_only": True, "non_binding": True}


def test_qa_cli_forwards_question_and_prints_json(monkeypatch) -> None:
    calls = {}

    async def fake_run_pipeline(**kwargs):
        calls.update(kwargs)
        return _FakeResult()

    monkeypatch.setattr(cli_module, "run_pipeline", fake_run_pipeline)
    result = CliRunner().invoke(cli_module.app, ["qa", "soru", "--jurisdiction-hint", "hukuk"])

    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["non_binding"] is True
    assert calls == {
        "question": "soru",
        "mode": "layered",
        "jurisdiction_hint": "hukuk",
        "synthesize": False,
    }


def test_qa_cli_rejects_empty_question_and_invalid_mode() -> None:
    runner = CliRunner()
    assert runner.invoke(cli_module.app, ["qa", ""]).exit_code != 0
    assert runner.invoke(cli_module.app, ["qa", "soru", "--mode", "unknown"]).exit_code != 0
```

- [ ] **Step 2: Run focused tests and confirm missing CLI/pipeline import failure**

Run: `uv run --no-cache pytest legalai/tests/cli/test_qa_cli.py -q`

Expected: FAIL because the `qa` command and CLI module's `run_pipeline` binding are missing.

- [ ] **Step 3: Implement the smallest CLI command**

Import `asyncio`, `json`, `run_pipeline`, and `typer.Argument`. Add a `qa` command that validates `question.strip()` and `mode in {"layered", "simple"}`, calls `asyncio.run(run_pipeline(question=question, mode=mode, jurisdiction_hint=jurisdiction_hint, synthesize=False))`, and prints `json.dumps(result.to_dict(), ensure_ascii=False, indent=2)`. Raise `typer.BadParameter` for invalid input.

- [ ] **Step 4: Run focused tests and verify pass**

Run: `uv run --no-cache pytest legalai/tests/cli/test_qa_cli.py -q`

Expected: `2 passed`.

- [ ] **Step 5: Commit**

```powershell
git add legalai/apps/cli/main.py legalai/tests/cli/test_qa_cli.py
git commit -m "feat: add legalai qa helper command"
```

### Task 3: IDE-first onboarding and reproducible demo documentation

**Files:**
- Modify: `README.md`
- Create: `CONTRIBUTING.md`
- Create: `docs/week11-demo.md`
- Modify: `docs/mcp-client-setup.md` only if the new health-check or CLI instructions need a cross-reference

**Interfaces:** Documentation only; no client-specific config overwrites.

- [ ] **Step 1: Write documentation acceptance tests**

Create `legalai/tests/apps/test_week11_docs.py`:

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def test_week11_docs_are_ide_first_and_secret_free() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    demo = (ROOT / "docs" / "week11-demo.md").read_text(encoding="utf-8")
    contributing = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")

    combined = "\n".join((readme, demo, contributing))
    for client in ("Codex", "Cursor", "Claude", "Antigravity", "VS Code"):
        assert client in combined
    for marker in ("legalai_saglik_kontrolu", "legalai_yardim", "Yalın", "Yönlendirilmiş", "Rafine"):
        assert marker in combined
    assert "OPENROUTER_API_KEY=" not in combined
    assert "DEEPSEEK_API_KEY=" not in combined
    assert "10000000146" not in combined
```

- [ ] **Step 2: Run the test and confirm missing-document failure**

Run: `uv run --no-cache pytest legalai/tests/apps/test_week11_docs.py -q`

Expected: FAIL because `CONTRIBUTING.md` and `docs/week11-demo.md` do not yet exist or required markers are absent.

- [ ] **Step 3: Write the minimal user-facing documents**

README must include a five-minute setup, an IDE-first supported-client table, a Mermaid flow, four module descriptions, `legalai_saglik_kontrolu`, `legalai_yardim`, `legalai qa`, and a contribution link. `docs/week11-demo.md` must explain the five IDE steps and provide three copy/paste Turkish prompts with expected output headings. `CONTRIBUTING.md` must document `uv sync --frozen --dev`, both test commands, secret/PII rules, and a PR checklist.

- [ ] **Step 4: Run documentation tests and verify pass**

Run: `uv run --no-cache pytest legalai/tests/apps/test_week11_docs.py -q`

Expected: `1 passed`.

- [ ] **Step 5: Commit**

```powershell
git add README.md CONTRIBUTING.md docs/week11-demo.md docs/mcp-client-setup.md legalai/tests/apps/test_week11_docs.py
git commit -m "docs: add ide-first week 11 onboarding"
```

### Task 4: Full verification and MCP metadata smoke test

**Files:**
- Modify: `docs/superpowers/plans/2026-07-17-week11-kesif-demo.md` to record execution status only after successful verification.

- [ ] **Step 1: Run targeted tests for all new behavior**

Run: `uv run --no-cache pytest legalai/tests/apps/test_mcp_health.py legalai/tests/cli/test_qa_cli.py legalai/tests/apps/test_week11_docs.py -q`

Expected: all targeted tests pass.

- [ ] **Step 2: Run full project tests with both supported execution paths**

Run: `.venv\Scripts\python.exe -m pytest -q` and `uv run --no-cache pytest -q`.

Expected: both commands exit 0 with zero failures.

- [ ] **Step 3: Run the MCP metadata smoke test**

Run:

```powershell
uv run --no-cache python -c "import json, asyncio; from legalai.apps.mcp import server; print(asyncio.run(server.legalai_saglik_kontrolu())); print(asyncio.run(server.legalai_yardim())['capabilities'][0]['id']); print('capabilities' in server.legalai_capabilities_resource())"
```

Expected: health payload has `external_calls: False`, the capability id is printed, and the final line is `True`.

- [ ] **Step 4: Run repository hygiene checks**

Run: `git diff --check`; then scan changed documentation for secrets and user-specific paths.

- [ ] **Step 5: Record status and prepare checkpoint**

Update this plan's execution status with exact test counts. Do not stage `.cursor/mcp.json` or `.superpowers/`. Offer the user the Cursor push command and merge sequence after verification.

## Execution status

- [ ] Task 1: health-check
- [ ] Task 2: `legalai qa`
- [ ] Task 3: IDE-first docs/demo/contributing
- [ ] Task 4: verification and checkpoint
