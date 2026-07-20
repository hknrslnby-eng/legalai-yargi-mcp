"""Resolve stable launch commands for source checkouts and portable bundles."""

import os
from pathlib import Path

from .models import McpLaunchSpec


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
    )
