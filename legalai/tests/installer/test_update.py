import hashlib
import json
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from legalai.packages.installer.update import (
    UpdateError,
    apply_update,
    check_for_update,
    check_remote_update,
    default_manifest_url,
    fetch_release_manifest,
    load_release_manifest,
    rollback_update,
)
from legalai.packages.installer.versioning import compare_versions
from legalai.apps.cli.main import app
from typer.testing import CliRunner


runner = CliRunner()


def _manifest(archive: Path, version: str = "1.1.0") -> dict[str, str]:
    return {
        "version": version,
        "channel": "stable",
        "release_url": "https://example.test/release",
        "archive_name": archive.name,
        "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "data_schema_version": "1",
        "minimum_supported_version": "1.0.0",
    }


def test_manifest_is_strict_and_versions_are_comparable(tmp_path: Path) -> None:
    archive = tmp_path / "release.zip"
    archive.write_bytes(b"release")
    manifest = load_release_manifest(_manifest(archive))

    assert manifest.version == "1.1.0"
    assert compare_versions("1.0.0", manifest.version) < 0
    with pytest.raises(UpdateError):
        load_release_manifest({"version": "1.1.0"})


def test_update_check_is_metadata_only_and_rate_limited(tmp_path: Path) -> None:
    state = tmp_path / "update-check.json"
    archive = tmp_path / "release.zip"
    archive.write_bytes(b"release")
    manifest = _manifest(archive)
    calls = []

    first = check_for_update(
        "1.0.0", lambda: calls.append(True) or manifest, state_path=state,
        now=datetime.now(timezone.utc), interval=timedelta(hours=24),
    )
    second = check_for_update(
        "1.0.0", lambda: calls.append(True) or manifest, state_path=state,
        now=datetime.now(timezone.utc) + timedelta(hours=1), interval=timedelta(hours=24),
    )

    assert first.available is True
    assert second.from_cache is True
    assert len(calls) == 1
    assert "document" not in json.dumps(json.loads(state.read_text(encoding="utf-8"))).lower()


def test_apply_update_verifies_checksum_and_preserves_data(tmp_path: Path) -> None:
    active_app = tmp_path / "app"
    active_app.mkdir()
    (active_app / "old.txt").write_text("old", encoding="utf-8")
    data = tmp_path / "data"
    data.mkdir()
    (data / "private.db").write_text("keep", encoding="utf-8")
    archive = tmp_path / "release.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("app/new.txt", "new")
    manifest = load_release_manifest(_manifest(archive))

    apply_update(archive, active_app, manifest)

    assert (active_app / "new.txt").read_text(encoding="utf-8") == "new"
    assert (data / "private.db").read_text(encoding="utf-8") == "keep"
    assert (tmp_path / "app.previous" / "old.txt").exists()


def test_failed_startup_validation_rolls_back(tmp_path: Path) -> None:
    active_app = tmp_path / "app"
    active_app.mkdir()
    (active_app / "old.txt").write_text("old", encoding="utf-8")
    archive = tmp_path / "release.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("app/new.txt", "new")
    manifest = load_release_manifest(_manifest(archive))

    with pytest.raises(UpdateError):
        apply_update(archive, active_app, manifest, validator=lambda _: False)

    assert (active_app / "old.txt").read_text(encoding="utf-8") == "old"


def test_failed_first_install_does_not_leave_new_app(tmp_path: Path) -> None:
    active_app = tmp_path / "app"
    archive = tmp_path / "release.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("app/new.txt", "new")
    manifest = load_release_manifest(_manifest(archive))

    with pytest.raises(UpdateError):
        apply_update(archive, active_app, manifest, validator=lambda _: False)

    assert not active_app.exists()


def test_explicit_rollback_restores_previous_app(tmp_path: Path) -> None:
    active_app = tmp_path / "app"
    previous = tmp_path / "app.previous"
    active_app.mkdir()
    previous.mkdir()
    (active_app / "new.txt").write_text("new", encoding="utf-8")
    (previous / "old.txt").write_text("old", encoding="utf-8")

    rollback_update(active_app)

    assert (active_app / "old.txt").exists()
    assert not active_app.joinpath("new.txt").exists()


def test_cli_update_check_reads_metadata_manifest(tmp_path: Path) -> None:
    archive = tmp_path / "release.zip"
    archive.write_bytes(b"release")
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(_manifest(archive, "9.0.0")), encoding="utf-8")

    result = runner.invoke(app, ["update", "check", "--manifest-file", str(manifest_path), "--state-path", str(tmp_path / "state.json")])

    assert result.exit_code == 0
    assert "available" in result.stdout


def test_default_manifest_url_is_platform_specific() -> None:
    assert default_manifest_url("windows-x64").endswith(
        "/releases/latest/download/release-manifest-windows-x64.json"
    )


def test_fetch_release_manifest_decodes_json_without_contract_text() -> None:
    manifest = {"version": "1.0.0", "channel": "stable"}

    payload = fetch_release_manifest(
        "https://example.test/manifest.json",
        get=lambda _url: json.dumps(manifest).encode("utf-8"),
    )

    assert payload == manifest


def test_fetch_release_manifest_requires_https_and_limits_metadata_size() -> None:
    with pytest.raises(UpdateError):
        fetch_release_manifest("http://example.test/manifest.json", get=lambda _url: b"{}")
    with pytest.raises(UpdateError):
        fetch_release_manifest("https://example.test/manifest.json", get=lambda _url: b"x" * (1024 * 1024 + 1))


def test_remote_update_check_uses_cache_and_never_downloads_archive(tmp_path: Path) -> None:
    archive = tmp_path / "release.zip"
    archive.write_bytes(b"release")
    manifest = _manifest(archive, "9.0.0")
    calls: list[str] = []

    result = check_remote_update(
        "1.0.0",
        manifest_url="https://example.test/manifest.json",
        state_path=tmp_path / "state.json",
        get=lambda url: calls.append(url) or json.dumps(manifest).encode("utf-8"),
    )

    assert result.available is True
    assert calls == ["https://example.test/manifest.json"]
    assert archive.name not in calls[0]
