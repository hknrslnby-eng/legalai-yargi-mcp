"""LegalAI local administrative CLI."""
from __future__ import annotations

import asyncio
import json

import typer

from legalai.packages.layers.analysis_pipeline import run_pipeline
from legalai.packages.shared.settings import settings
from legalai.packages.usage.store import UsageStore


app = typer.Typer(help="LegalAI yerel yönetim araçları.", no_args_is_help=True)
usage_app = typer.Typer(help="LLM kullanım raporları.", no_args_is_help=True)
app.add_typer(usage_app, name="usage")
_QA_MODES = {"layered", "simple"}


@app.command("qa")
def qa(
    question: str = typer.Argument(..., help="Analiz edilecek hukuki soru"),
    mode: str = typer.Option("layered", "--mode", help="Analiz seviyesi: layered veya simple"),
    jurisdiction_hint: str | None = typer.Option(
        None,
        "--jurisdiction-hint",
        help="İsteğe bağlı yargı türü veya hukuk alanı ipucu",
    ),
) -> None:
    """Yerel host model için API anahtarsız katmanlı analiz paketi üretir."""
    if not question.strip():
        raise typer.BadParameter("Soru boş olamaz.", param_hint="question")
    if mode not in _QA_MODES:
        raise typer.BadParameter(
            "mode layered veya simple olmalıdır.",
            param_hint="--mode",
        )

    result = asyncio.run(
        run_pipeline(
            question=question,
            mode=mode,
            jurisdiction_hint=jurisdiction_hint,
            synthesize=False,
        )
    )
    typer.echo(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))


@usage_app.command("report")
def usage_report(
    month: str = typer.Option(..., "--month", help="Rapor ayı: YYYY-MM"),
    tenant_id: str | None = typer.Option(None, "--tenant-id", help="İsteğe bağlı tenant filtresi"),
) -> None:
    """Print a tenant-scoped monthly usage report as JSON."""
    report = asyncio.run(UsageStore(settings.usage_db_path).report(month, tenant_id=tenant_id))
    typer.echo(json.dumps(report, ensure_ascii=False, indent=2))


def main() -> None:
    app()
