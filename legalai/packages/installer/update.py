"""Explicit, checksum-verified update and rollback lifecycle."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tarfile
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

from .versioning import compare_versions


class UpdateError(ValueError):
    """An update could not be verified, applied, or rolled back safely."""


@dataclass(frozen=True)
class ReleaseManifest:
    version: str
    channel: str
    release_url: str
    archive_name: str
    sha256: str
    data_schema_version: str
    minimum_supported_version: str


@dataclass(frozen=True)
class UpdateCheckResult:
    available: bool
    manifest: ReleaseManifest | None
    from_cache: bool
    checked_at: datetime


_REQUIRED_FIELDS = {
    "version", "channel", "release_url", "archive_name", "sha256",
    "data_schema_version", "minimum_supported_version",
}


def load_release_manifest(payload: dict[str, object]) -> ReleaseManifest:
    missing = _REQUIRED_FIELDS - payload.keys()
    if missing:
        raise UpdateError(f"Release manifest alanları eksik: {', '.join(sorted(missing))}")
    values = {key: payload[key] for key in _REQUIRED_FIELDS}
    if not all(isinstance(value, str) and value.strip() for value in values.values()):
        raise UpdateError("Release manifest alanları boş olmayan metin olmalıdır.")
    sha256 = values["sha256"]
    if len(sha256) != 64 or any(character not in "0123456789abcdefABCDEF" for character in sha256):
        raise UpdateError("Release manifest sha256 alanı geçersiz.")
    try:
        compare_versions(values["version"], values["minimum_supported_version"])
    except ValueError as error:
        raise UpdateError(str(error)) from error
    return ReleaseManifest(**values)


def _read_cached(path: Path, now: datetime) -> tuple[ReleaseManifest, datetime] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        checked_at = datetime.fromisoformat(payload["checked_at"])
        manifest = load_release_manifest(payload["manifest"])
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError, UpdateError):
        return None
    return manifest, checked_at


def check_for_update(
    current_version: str,
    fetch_manifest: Callable[[], dict[str, object]],
    *,
    state_path: Path,
    now: datetime | None = None,
    interval: timedelta = timedelta(hours=24),
) -> UpdateCheckResult:
    now = now or datetime.now(timezone.utc)
    cached = _read_cached(state_path, now)
    if cached and now - cached[1] < interval:
        manifest, checked_at = cached
        return UpdateCheckResult(compare_versions(current_version, manifest.version) < 0, manifest, True, checked_at)
    manifest = load_release_manifest(fetch_manifest())
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps({"checked_at": now.isoformat(), "manifest": manifest.__dict__}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return UpdateCheckResult(compare_versions(current_version, manifest.version) < 0, manifest, False, now)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_destination(root: Path, member_name: str) -> Path:
    destination = (root / member_name).resolve()
    if destination != root and root not in destination.parents:
        raise UpdateError("Güncelleme arşivi güvenli olmayan bir yol içeriyor.")
    return destination


def _extract(archive: Path, destination: Path) -> None:
    if archive.suffix == ".zip":
        with zipfile.ZipFile(archive) as handle:
            for member in handle.infolist():
                target = _safe_destination(destination, member.filename)
                if member.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(handle.read(member))
        return
    if archive.name.endswith(".tar.gz"):
        with tarfile.open(archive, "r:gz") as handle:
            for member in handle.getmembers():
                target = _safe_destination(destination, member.name)
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                elif member.isfile():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with handle.extractfile(member) as source:
                        assert source is not None
                        target.write_bytes(source.read())
        return
    raise UpdateError("Desteklenmeyen portable arşiv biçimi.")


def apply_update(
    archive: Path,
    active_app: Path,
    manifest: ReleaseManifest,
    *,
    validator: Callable[[Path], bool] | None = None,
) -> None:
    archive = Path(archive)
    active_app = Path(active_app)
    if archive.name != manifest.archive_name:
        raise UpdateError("Arşiv adı release manifest ile eşleşmiyor.")
    if _sha256(archive).lower() != manifest.sha256.lower():
        raise UpdateError("SHA-256 doğrulaması başarısız; aktif uygulama değiştirilmedi.")

    stage_parent = Path(tempfile.mkdtemp(prefix=".socratlegal-update-", dir=active_app.parent))
    staged_root: Path | None = None
    previous = active_app.with_name(f"{active_app.name}.previous")
    try:
        _extract(archive, stage_parent)
        staged_root = stage_parent / "app" if (stage_parent / "app").is_dir() else stage_parent
        if previous.exists():
            shutil.rmtree(previous)
        if active_app.exists():
            shutil.move(str(active_app), str(previous))
        shutil.move(str(staged_root), str(active_app))
        if validator is not None and not validator(active_app):
            raise UpdateError("Yeni sürüm başlangıç doğrulamasını geçemedi; geri alındı.")
    except Exception as error:
        if active_app.exists() and previous.exists():
            shutil.rmtree(active_app)
            shutil.move(str(previous), str(active_app))
        elif active_app.exists():
            shutil.rmtree(active_app)
        if isinstance(error, UpdateError):
            raise
        raise UpdateError(f"Güncelleme uygulanamadı: {error}") from error
    finally:
        if stage_parent.exists():
            shutil.rmtree(stage_parent, ignore_errors=True)


def rollback_update(active_app: Path) -> None:
    active_app = Path(active_app)
    previous = active_app.with_name(f"{active_app.name}.previous")
    if not previous.is_dir():
        raise UpdateError("Geri alınabilecek bir önceki uygulama sürümü bulunamadı.")
    failed = active_app.with_name(f"{active_app.name}.failed")
    if failed.exists():
        shutil.rmtree(failed)
    if active_app.exists():
        shutil.move(str(active_app), str(failed))
    shutil.move(str(previous), str(active_app))
    if failed.exists():
        shutil.rmtree(failed)
