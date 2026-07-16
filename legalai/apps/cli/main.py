"""LegalAI local administrative CLI."""
from __future__ import annotations

import asyncio
import json

import typer

from legalai.packages.shared.settings import settings
from legalai.packages.usage.store import UsageStore


app = typer.Typer(help="LegalAI yerel yönetim araçları.", no_args_is_help=True)
usage_app = typer.Typer(help="LLM kullanım raporları.", no_args_is_help=True)
app.add_typer(usage_app, name="usage")


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

