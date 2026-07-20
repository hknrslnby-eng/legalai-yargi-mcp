"""Build portable archives without bundling user state or credentials."""

from __future__ import annotations

import fnmatch
import hashlib
import argparse
import json
import shutil
import tarfile
import zipfile
from pathlib import Path


EXCLUDED_NAMES = {".venv", ".env", "data", "logs", ".git", ".cursor", ".codex", ".superpowers", "__pycache__"}
EXCLUDED_PATTERNS = ("*.sqlite", "*.db", "*.jsonl", "*.pyc")
ROOT_ASSETS = {"install.ps1", "install.sh", "start.cmd", "start.sh", "portable-manifest.json"}


def _excluded(relative: Path) -> bool:
    if any(part in EXCLUDED_NAMES for part in relative.parts):
        return True
    return any(fnmatch.fnmatch(relative.name, pattern) for pattern in EXCLUDED_PATTERNS)


def _files(source: Path) -> list[Path]:
    return sorted(
        (path for path in source.rglob("*") if path.is_file() and not _excluded(path.relative_to(source))),
        key=lambda path: path.relative_to(source).as_posix(),
    )


def _write_checksum(archive: Path) -> None:
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_name(f"{archive.name}.sha256").write_text(f"{digest}  {archive.name}\n", encoding="utf-8")


def write_release_manifest(
    archive: Path,
    output: Path,
    *,
    version: str,
    release_url: str,
    channel: str = "stable",
    data_schema_version: str = "1",
    minimum_supported_version: str = "0.1.0",
) -> dict[str, str]:
    payload = {
        "version": version,
        "channel": channel,
        "release_url": release_url,
        "archive_name": archive.name,
        "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "data_schema_version": data_schema_version,
        "minimum_supported_version": minimum_supported_version,
    }
    Path(output).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def prepare_portable_tree(source: Path, destination: Path, runtime_binary: Path) -> None:
    """Create ``app``/``runtime`` layout while keeping launchers at the root."""

    source = Path(source).resolve()
    destination = Path(destination).resolve()
    if destination.exists():
        shutil.rmtree(destination)
    app = destination / "app"
    runtime = destination / "runtime"
    app.mkdir(parents=True)
    runtime.mkdir()
    for item in source.iterdir():
        if item.name in EXCLUDED_NAMES or item.name in {"dist", "runtime", "portable"}:
            continue
        if item.name == "scripts":
            for asset in item.iterdir():
                if asset.name in ROOT_ASSETS:
                    shutil.copy2(asset, destination / asset.name)
            continue
        target = app / item.name
        if item.is_dir():
            shutil.copytree(item, target, ignore=shutil.ignore_patterns(*EXCLUDED_NAMES, "*.sqlite", "*.db", "*.jsonl", "*.pyc"))
        else:
            shutil.copy2(item, target)
    shutil.copy2(runtime_binary, runtime / Path(runtime_binary).name)


def build_portable_archive(source: Path, output_dir: Path, *, platform_tag: str, version: str) -> Path:
    source = Path(source).resolve()
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    files = _files(source)
    if platform_tag.lower().startswith(("windows", "win")):
        archive = output_dir / f"socratlegal-{version}-{platform_tag}.zip"
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as handle:
            for path in files:
                handle.write(path, path.relative_to(source).as_posix())
    else:
        archive = output_dir / f"socratlegal-{version}-{platform_tag}.tar.gz"
        with tarfile.open(archive, "w:gz") as handle:
            for path in files:
                handle.add(path, arcname=path.relative_to(source).as_posix())
    _write_checksum(archive)
    return archive


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a SocratLegal portable archive")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--platform-tag", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--release-url", default="")
    args = parser.parse_args()
    staging = args.output / f"staging-{args.platform_tag}"
    prepare_portable_tree(args.source, staging, args.runtime)
    archive = build_portable_archive(staging, args.output, platform_tag=args.platform_tag, version=args.version)
    if args.release_url:
        write_release_manifest(
            archive,
            args.output / f"release-manifest-{args.platform_tag}.json",
            version=args.version,
            release_url=args.release_url,
        )


if __name__ == "__main__":
    main()
