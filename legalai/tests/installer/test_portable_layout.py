import json
from pathlib import Path


ROOT = Path(__file__).parents[3]


def test_portable_layout_has_cross_platform_launchers() -> None:
    for name in ("scripts/install.ps1", "scripts/install.sh", "scripts/start.cmd", "scripts/start.sh"):
        assert (ROOT / name).exists(), name


def test_portable_manifest_pins_runtime_and_excludes_user_state() -> None:
    manifest = json.loads((ROOT / "scripts/portable-manifest.json").read_text(encoding="utf-8"))
    assert manifest["product"] == "SocratLegal"
    assert manifest["runtime"]["name"] == "uv"
    assert manifest["runtime"]["version"]
    assert "data" in manifest["exclude"]
    assert ".env" in manifest["exclude"]
