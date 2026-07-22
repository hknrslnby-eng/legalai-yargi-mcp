import tarfile
import zipfile
from pathlib import Path

from scripts.package_portable import build_portable_archive, prepare_portable_tree, write_release_manifest


def test_package_excludes_user_state_and_includes_runtime(tmp_path: Path) -> None:
    source = tmp_path / "source"
    output = tmp_path / "dist"
    (source / "app").mkdir(parents=True)
    (source / "legalai").mkdir()
    (source / "runtime").mkdir()
    (source / "data").mkdir()
    (source / "app" / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (source / "legalai" / "__init__.py").write_text('__version__ = "0.2.5"\n', encoding="utf-8")
    (source / "runtime" / "uv.exe").write_bytes(b"runtime")
    (source / "data" / "private.db").write_bytes(b"private")
    (source / ".env").write_text("SECRET=do-not-package", encoding="utf-8")

    archive = build_portable_archive(source, output, platform_tag="windows-x64", version="0.1.0")

    assert archive.exists()
    with zipfile.ZipFile(archive) as handle:
        names = set(handle.namelist())
        runtime_version = handle.read("legalai/__init__.py").decode("utf-8")
    assert "app/pyproject.toml" in names
    assert '__version__ = "0.2.5"' in runtime_version
    assert "runtime/uv.exe" in names
    assert not any(name.startswith("data/") or name == ".env" for name in names)


def test_package_can_create_tar_gz_for_unix(tmp_path: Path) -> None:
    source = tmp_path / "source"
    output = tmp_path / "dist"
    (source / "app").mkdir(parents=True)
    (source / "app" / "README.md").write_text("portable", encoding="utf-8")

    archive = build_portable_archive(source, output, platform_tag="linux-x64", version="0.1.0")

    assert archive.suffixes[-2:] == [".tar", ".gz"]
    with tarfile.open(archive, "r:gz") as handle:
        assert "app/README.md" in handle.getnames()


def test_prepare_tree_places_application_and_runtime_in_stable_locations(tmp_path: Path) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "portable"
    (source / "legalai").mkdir(parents=True)
    (source / "scripts").mkdir()
    (source / "legalai" / "__init__.py").write_text("", encoding="utf-8")
    (source / "scripts" / "start.cmd").write_text("start", encoding="utf-8")
    runtime = tmp_path / "uv.exe"
    runtime.write_bytes(b"uv")

    prepare_portable_tree(source, destination, runtime)

    assert (destination / "app" / "legalai" / "__init__.py").exists()
    assert (destination / "runtime" / "uv.exe").exists()
    assert (destination / "start.cmd").exists()


def test_release_manifest_contains_archive_checksum(tmp_path: Path) -> None:
    archive = tmp_path / "socratlegal-1.0.0-windows-x64.zip"
    archive.write_bytes(b"archive")

    manifest = write_release_manifest(
        archive,
        tmp_path / "release.json",
        version="1.0.0",
        release_url="https://example.test/release",
    )

    assert manifest["archive_name"] == archive.name
    assert len(manifest["sha256"]) == 64


def test_release_workflow_guards_version_before_packaging() -> None:
    root = Path(__file__).resolve().parents[3]
    workflow = (root / ".github" / "workflows" / "portable-release.yml").read_text(encoding="utf-8")

    assert "check_release_version.py" in workflow
    assert "legalai/tests/installer legalai/tests/apps" in workflow
    assert workflow.index("check_release_version.py") < workflow.index("package_portable.py")
