from importlib.metadata import version

from legalai import __version__
from legalai.apps.api.app import app as api_app
from legalai.apps.mcp.server import app as mcp_app


def test_runtime_surfaces_report_package_version() -> None:
    package_version = version("yargi-mcp")

    assert package_version == "0.2.5"
    assert __version__ == package_version
    assert api_app.version == package_version
    assert mcp_app.version == package_version
