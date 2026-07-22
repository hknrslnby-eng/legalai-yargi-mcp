"""Resolve stable launch commands for source checkouts and portable bundles."""

import os
from pathlib import Path

from .models import McpLaunchSpec


def portable_config_path(bundle_root: Path) -> Path:
    """Return the portable bundle's user-editable configuration directory."""

    return Path(bundle_root).resolve() / "config"


def portable_data_path(bundle_root: Path) -> Path:
    """Return the portable bundle's persistent user-data directory."""

    return Path(bundle_root).resolve() / "data"


def prepare_env_file(bundle_root: Path) -> Path:
    """Create a blank portable env file without overwriting user settings."""

    bundle_root = Path(bundle_root).resolve()
    config_dir = portable_config_path(bundle_root)
    config_dir.mkdir(parents=True, exist_ok=True)
    env_path = config_dir / ".env"
    if env_path.exists():
        return env_path

    example_candidates = (
        bundle_root / "app" / "legalai.env.example",
        bundle_root / "legalai.env.example",
    )
    example = next((candidate for candidate in example_candidates if candidate.exists()), None)
    content = example.read_text(encoding="utf-8") if example else "# SocratLegal API anahtarları; boş bırakılabilir.\n"
    # Portable processes run from app/, so persistent paths point to the
    # sibling data directory instead of creating hidden state inside app/.
    content = content.replace("STORAGE_ROOT=./.data", "STORAGE_ROOT=../data")
    content = content.replace("DATABASE_URL=sqlite+aiosqlite:///./.data/", "DATABASE_URL=sqlite+aiosqlite:///../data/")
    content = content.replace("CORPUS_DB_PATH=./.data/", "CORPUS_DB_PATH=../data/")
    content = content.replace("USAGE_DB_PATH=./.data/", "USAGE_DB_PATH=../data/")
    content = content.replace("PII_MAP_DB_PATH=./.data/", "PII_MAP_DB_PATH=../data/")
    env_path.write_text(content, encoding="utf-8")
    portable_data_path(bundle_root).mkdir(parents=True, exist_ok=True)
    return env_path


def resolve_data_dir(install_dir: Path, explicit: Path | None = None) -> Path:
    """Return the user data directory, preferring an explicit location."""

    return explicit if explicit is not None else install_dir / "data"


def _python_executable(project_dir: Path) -> Path:
    relative = Path(".venv") / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    return project_dir / relative


def _portable_uv(portable_root: Path) -> Path:
    return portable_root / "runtime" / ("uv.exe" if os.name == "nt" else "uv")


def build_checkout_launch_spec(project_dir: Path) -> McpLaunchSpec:
    project_dir = project_dir.resolve()
    return McpLaunchSpec(
        name="socratlegal",
        command=str(_python_executable(project_dir)),
        args=("-m", "legalai.apps.mcp.server"),
        cwd=str(project_dir),
    )


def build_portable_launch_spec(portable_root: Path) -> McpLaunchSpec:
    portable_root = portable_root.resolve()
    app_dir = portable_root / "app"
    return McpLaunchSpec(
        name="socratlegal",
        command=str(_portable_uv(portable_root)),
        args=("run", "--directory", str(app_dir), "socratlegal-mcp"),
        cwd=str(app_dir),
        env={"SOCRATLEGAL_ENV_FILE": str(portable_config_path(portable_root) / ".env")},
    )
