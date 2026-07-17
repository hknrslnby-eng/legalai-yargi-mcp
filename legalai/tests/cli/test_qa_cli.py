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

    monkeypatch.setattr(cli_module, "run_pipeline", fake_run_pipeline, raising=False)
    result = CliRunner().invoke(
        cli_module.app,
        ["qa", "soru", "--jurisdiction-hint", "hukuk"],
    )

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
