import json
from datetime import datetime, timezone

from typer.testing import CliRunner

from legalai.apps.cli.main import app
from legalai.packages.shared.settings import settings
from legalai.packages.usage.store import UsageStore


def test_usage_report_cli_prints_json_for_selected_tenant(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "usage.db"
    monkeypatch.setattr(settings, "usage_db_path", str(db_path))

    import asyncio

    asyncio.run(
        UsageStore(db_path).record(
            tenant_id="local",
            model="gemini-2.5-pro",
            input_tokens=10,
            output_tokens=5,
            cost_usd_estimate=0.0001,
            ts=datetime(2026, 7, 10, tzinfo=timezone.utc),
        )
    )

    result = CliRunner().invoke(
        app,
        ["usage", "report", "--month", "2026-07", "--tenant-id", "local"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["tenant_id"] == "local"
    assert payload["calls"] == 1
    assert payload["input_tokens"] == 10

