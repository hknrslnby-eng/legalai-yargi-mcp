import pathlib

import pytest

from legalai.packages.aihm.cache import get_cached, set_cached


@pytest.mark.asyncio
async def test_cache_roundtrip(tmp_path: pathlib.Path):
    db_path = tmp_path / "aihm_cache_test.db"
    payload = {"application_no": "47533/99", "sections": {"procedure": "..."}}

    assert await get_cached("appno:47533/99:ENG", db_path=db_path) is None

    await set_cached("appno:47533/99:ENG", payload, db_path=db_path)
    cached = await get_cached("appno:47533/99:ENG", db_path=db_path)

    assert cached == payload


@pytest.mark.asyncio
async def test_cache_expires_after_ttl(tmp_path: pathlib.Path, monkeypatch):
    import legalai.packages.aihm.cache as cache_module

    db_path = tmp_path / "aihm_cache_ttl_test.db"
    await set_cached("expired-key", {"x": 1}, db_path=db_path)

    monkeypatch.setattr(cache_module, "TTL_SECONDS", -1)  # her şeyi süresi dolmuş yap

    assert await get_cached("expired-key", db_path=db_path) is None
