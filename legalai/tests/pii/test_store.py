import pathlib

import pytest

from legalai.packages.pii.store import get_token, put_token


@pytest.mark.asyncio
async def test_put_and_get_token_roundtrip(tmp_path: pathlib.Path):
    db_path = tmp_path / "pii_map_test.db"

    assert await get_token("local", "TCKN_1", db_path) is None

    await put_token("local", "TCKN_1", "encrypted-value", "wrapped-dek", db_path)
    row = await get_token("local", "TCKN_1", db_path)

    assert row == ("encrypted-value", "wrapped-dek")


@pytest.mark.asyncio
async def test_get_token_is_isolated_per_tenant(tmp_path: pathlib.Path):
    db_path = tmp_path / "pii_map_isolation_test.db"

    await put_token("tenant_a", "TCKN_1", "value-a", "dek-a", db_path)
    await put_token("tenant_b", "TCKN_1", "value-b", "dek-b", db_path)

    assert await get_token("tenant_a", "TCKN_1", db_path) == ("value-a", "dek-a")
    assert await get_token("tenant_b", "TCKN_1", db_path) == ("value-b", "dek-b")
