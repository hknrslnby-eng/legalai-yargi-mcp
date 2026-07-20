"""LegalAI local administrative CLI."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from datetime import timedelta

import typer

from legalai.packages.layers.analysis_pipeline import run_pipeline
from legalai.packages.corpus.sources.official import build_default_priority_adapters
from legalai.packages.corpus.sync import CorpusSyncService
from legalai.packages.shared.settings import settings
from legalai.packages.usage.store import UsageStore
from legalai.packages.installer.ides import detect_ide_configs
from legalai.packages.installer.models import InstallRequest
from legalai.packages.installer.service import install_socratlegal
from legalai.packages.installer.update import (
    UpdateError,
    apply_update,
    check_for_update,
    check_remote_update,
    load_release_manifest,
    rollback_update,
)


app = typer.Typer(help="LegalAI yerel yönetim araçları.", no_args_is_help=True)
usage_app = typer.Typer(help="LLM kullanım raporları.", no_args_is_help=True)
app.add_typer(usage_app, name="usage")
_QA_MODES = {"layered", "simple"}
corpus_app = typer.Typer(help="SocratLegal local corpus tools", no_args_is_help=True)
app.add_typer(corpus_app, name="corpus")
update_app = typer.Typer(help="SocratLegal sürüm güncelleme araçları", no_args_is_help=True)
app.add_typer(update_app, name="update")


@update_app.command("check")
def update_check(
    manifest_file: Path | None = typer.Option(None, "--manifest-file", help="Yerel release manifest JSON dosyası"),
    manifest_url: str | None = typer.Option(None, "--manifest-url", help="Release manifest metadata URL'si"),
    platform_tag: str | None = typer.Option(None, "--platform-tag", help="windows-x64, macos-arm64 veya linux-x64"),
    state_path: Path = typer.Option(Path.home() / ".socratlegal" / "update-check.json", "--state-path"),
    current_version: str = typer.Option("0.2.2", "--current-version"),
) -> None:
    """Yalnızca sürüm metadata'sını kontrol eder; arşiv indirme/kurma yapmaz."""
    if manifest_file and manifest_url:
        raise typer.BadParameter("--manifest-file ile --manifest-url birlikte kullanılamaz.")
    try:
        if manifest_file:
            payload = json.loads(manifest_file.read_text(encoding="utf-8"))
            result = check_for_update(current_version, lambda: payload, state_path=state_path)
        else:
            result = check_remote_update(
                current_version,
                manifest_url=manifest_url,
                platform_tag=platform_tag,
                state_path=state_path,
                interval=timedelta(hours=24),
            )
    except (OSError, json.JSONDecodeError, UpdateError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(json.dumps({
        "available": result.available,
        "version": result.manifest.version if result.manifest else None,
        "channel": result.manifest.channel if result.manifest else None,
        "from_cache": result.from_cache,
        "checked_at": result.checked_at.isoformat(),
    }, ensure_ascii=False, indent=2))


@update_app.command("apply")
def update_apply(
    archive: Path = typer.Option(..., "--archive"),
    manifest_file: Path = typer.Option(..., "--manifest-file"),
    active_app: Path = typer.Option(Path.cwd() / "app", "--active-app"),
) -> None:
    """Açıkça istenen, checksum doğrulamalı uygulama güncellemesini yapar."""
    manifest = load_release_manifest(json.loads(manifest_file.read_text(encoding="utf-8")))
    apply_update(archive, active_app, manifest)
    typer.echo(f"Güncelleme uygulandı: {manifest.version}")


@update_app.command("rollback")
def update_rollback(active_app: Path = typer.Option(Path.cwd() / "app", "--active-app")) -> None:
    """Son çalışan uygulama sürümüne geri döner."""
    rollback_update(active_app)
    typer.echo("Önceki SocratLegal sürümüne geri dönüldü.")


@app.command("install")
def install(
    install_dir: Path = typer.Option(Path.cwd(), "--install-dir", help="SocratLegal kaynak veya uygulama klasörü"),
    ide: list[str] = typer.Option([], "--ide", help="cursor, antigravity, vscode, claude veya codex; tekrarlanabilir"),
    portable_root: Path | None = typer.Option(None, "--portable-root", help="Portable klasörünün kökü"),
    data_dir: Path | None = typer.Option(None, "--data-dir", help="Belgeler ve yerel corpus için ayrı veri klasörü"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Dosyaya yazmadan ne yapılacağını göster"),
    repair: bool = typer.Option(False, "--repair", help="Bitişik iki JSON nesnesinden oluşan eski ayarı onarmayı dene"),
) -> None:
    """SocratLegal'i seçilen IDE'lere tek komutla bağlar."""
    known = {item.ide_id: item for item in detect_ide_configs(
        home=Path.home(),
        appdata=Path.home() / "AppData" / "Roaming",
        project_dir=install_dir,
    )}
    selected = list(known) if not ide or "all" in ide else ide
    unknown = [item for item in selected if item not in known]
    if unknown:
        raise typer.BadParameter(f"Bilinmeyen IDE: {', '.join(unknown)}", param_hint="--ide")
    request = InstallRequest(
        install_dir=install_dir,
        data_dir=data_dir,
        ide_ids=tuple(selected),
        portable_root=portable_root,
        dry_run=dry_run,
        repair=repair,
    )
    try:
        results = install_socratlegal(request, project_dir=install_dir)
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    for result in results:
        typer.echo(f"{result.ide_id}: {result.status} — {result.message} [{result.config_path}]")
    if portable_root:
        typer.echo("Portable çalışma yolu seçildi; sistem Python/uv kurulumu gerekmez.")
    else:
        typer.echo("Kaynak checkout yolu seçildi; mevcut .venv Python çalıştırıcısı kullanılacak.")


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


@corpus_app.command("status")
def corpus_status() -> None:
    """Show local SocratLegal corpus status."""
    typer.echo(json.dumps(asyncio.run(CorpusSyncService().status()), ensure_ascii=False, indent=2))


@corpus_app.command("sync")
def corpus_sync(
    query: str = typer.Option(..., "--query", help="Query sent to the configured official adapter."),
    source: str = typer.Option("all", "--source", help="all or a source id such as rekabet_kurumu, kik, kvkk."),
    limit: int = typer.Option(20, "--limit", min=1, max=100),
) -> None:
    """Mask a query, search configured official adapters, and persist results locally."""
    adapters = {adapter.source_id: adapter for adapter in build_default_priority_adapters()}
    selected = list(adapters) if source == "all" else [source]

    async def _run() -> list[dict]:
        service = CorpusSyncService()
        reports: list[dict] = []
        for source_id in selected:
            adapter = adapters.get(source_id)
            if adapter is None:
                reports.append({"source_id": source_id, "status": "unavailable_or_not_configured"})
                continue
            reports.append(await service.sync_from_adapter(source_id, adapter, query, limit))
        return reports

    typer.echo(json.dumps(asyncio.run(_run()), ensure_ascii=False, indent=2))


def main() -> None:
    app()
