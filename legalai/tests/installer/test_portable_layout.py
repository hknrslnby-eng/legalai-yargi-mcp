import json
from pathlib import Path

from legalai.packages.installer.paths import prepare_env_file, portable_config_path, portable_data_path

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


def test_portable_user_state_has_separate_config_and_data(tmp_path: Path) -> None:
    bundle = tmp_path / "portable"
    (bundle / "app").mkdir(parents=True)
    (bundle / "app" / "legalai.env.example").write_text(
        "OPENAI_API_KEY=\nSTORAGE_ROOT=./.data\nDATABASE_URL=sqlite+aiosqlite:///./.data/legalai.db\n",
        encoding="utf-8",
    )

    env_path = prepare_env_file(bundle)

    assert env_path == portable_config_path(bundle) / ".env"
    assert portable_data_path(bundle).is_dir()
    assert "OPENAI_API_KEY=" in env_path.read_text(encoding="utf-8")
    assert "STORAGE_ROOT=../data" in env_path.read_text(encoding="utf-8")
    env_path.write_text("OPENAI_API_KEY=user-key\n", encoding="utf-8")
    assert prepare_env_file(bundle).read_text(encoding="utf-8") == "OPENAI_API_KEY=user-key\n"
