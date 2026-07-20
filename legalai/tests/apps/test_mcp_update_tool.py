from datetime import datetime, timezone

import pytest

import legalai.apps.mcp.server as server_module
from legalai.packages.installer.update import ReleaseManifest, UpdateCheckResult


@pytest.mark.asyncio
async def test_update_tool_returns_metadata_without_applying_or_downloading(monkeypatch):
    manifest = ReleaseManifest(
        version="9.0.0",
        channel="stable",
        release_url="https://example.test/release",
        archive_name="socratlegal-9.0.0-windows-x64.zip",
        sha256="a" * 64,
        data_schema_version="1",
        minimum_supported_version="0.2.2",
    )

    def fake_check(*_args, **_kwargs):
        return UpdateCheckResult(True, manifest, False, datetime.now(timezone.utc))

    monkeypatch.setattr(server_module, "check_remote_update", fake_check)
    payload = await server_module.socratlegal_guncelleme_kontrol()

    assert payload["status"] == "ok"
    assert payload["available"] is True
    assert payload["archive_name"].endswith(".zip")
    assert payload["auto_apply"] is False
    assert payload["archive_downloaded"] is False


@pytest.mark.asyncio
async def test_update_tool_reports_metadata_errors_without_mutating_state(monkeypatch):
    def fake_check(*_args, **_kwargs):
        raise server_module.UpdateError("manifest yok")

    monkeypatch.setattr(server_module, "check_remote_update", fake_check)
    payload = await server_module.socratlegal_guncelleme_kontrol()

    assert payload == {
        "status": "error",
        "error": "manifest yok",
        "auto_apply": False,
        "archive_downloaded": False,
    }


def test_update_tool_is_discoverable_from_catalog():
    catalog = server_module.capability_catalog()

    assert catalog["active_public_tools"]["socratlegal_guncelleme_kontrol"] == "guncelleme_kontrol"
    assert any(item["id"] == "guncelleme_kontrol" for item in catalog["capabilities"])
