from pathlib import Path

from legalai.packages.installer.models import InstallResult, McpLaunchSpec
from legalai.packages.installer.paths import (
    build_checkout_launch_spec,
    build_portable_launch_spec,
    resolve_data_dir,
)


def test_explicit_data_directory_wins() -> None:
    assert resolve_data_dir(Path("C:/SocratLegal"), Path("D:/SocratData")) == Path("D:/SocratData")


def test_default_data_directory_is_inside_install_directory() -> None:
    assert resolve_data_dir(Path("C:/SocratLegal"), None) == Path("C:/SocratLegal/data")


def test_checkout_launch_uses_module_server() -> None:
    spec = build_checkout_launch_spec(Path("C:/SocratLegal"))
    assert isinstance(spec, McpLaunchSpec)
    assert spec.command.replace("\\", "/").endswith(".venv/Scripts/python.exe") or spec.command.replace("\\", "/").endswith(".venv/bin/python")
    assert spec.args == ("-m", "legalai.apps.mcp.server")
    assert spec.cwd == str(Path("C:/SocratLegal"))


def test_portable_launch_uses_bundled_uv() -> None:
    spec = build_portable_launch_spec(Path("C:/SocratLegal"))
    assert spec.command.replace("\\", "/").endswith("runtime/uv.exe") or spec.command.replace("\\", "/").endswith("runtime/uv")
    assert spec.args == ("run", "--directory", str(Path("C:/SocratLegal/app")), "socratlegal-mcp")
    assert spec.cwd == str(Path("C:/SocratLegal/app"))


def test_install_result_has_stable_shape() -> None:
    result = InstallResult("cursor", Path("C:/mcp.json"), "installed", None, "ok")
    assert result.status == "installed"
