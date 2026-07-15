import pathlib

import pytest

from legalai.packages.pii.gateway import PiiGateway

VALID_TCKN = "10000000146"


@pytest.mark.asyncio
async def test_mask_replaces_tckn_with_placeholder(tmp_path: pathlib.Path):
    gateway = PiiGateway(db_path=tmp_path / "pii_map.db")

    masked = await gateway.mask(f"Ahmet Yılmaz'ın TCKN'si {VALID_TCKN}'dir.")

    assert VALID_TCKN not in masked
    assert "[TCKN_1]" in masked


@pytest.mark.asyncio
async def test_mask_is_idempotent_for_repeated_values(tmp_path: pathlib.Path):
    gateway = PiiGateway(db_path=tmp_path / "pii_map.db")

    text = f"{VALID_TCKN} ve tekrar {VALID_TCKN}"
    masked = await gateway.mask(text)

    assert masked.count("[TCKN_1]") == 2


@pytest.mark.asyncio
async def test_unmask_restores_original_value_within_same_process(tmp_path: pathlib.Path):
    gateway = PiiGateway(db_path=tmp_path / "pii_map.db")

    original = f"TCKN: {VALID_TCKN}"
    masked = await gateway.mask(original)
    restored = await gateway.unmask(masked)

    assert restored == original


@pytest.mark.asyncio
async def test_unmask_from_store_restores_value_using_only_sqlite(tmp_path: pathlib.Path):
    db_path = tmp_path / "pii_map.db"
    gateway = PiiGateway(db_path=db_path)

    original = f"TCKN: {VALID_TCKN}"
    masked = await gateway.mask(original)

    # Süreç-içi önbelleği simüle etmek için temizle — sadece SQLite kalsın
    from legalai.packages.pii.gateway import _consistency_cache

    _consistency_cache.clear()

    restored = await gateway.unmask_from_store(masked)
    assert restored == original


@pytest.mark.asyncio
async def test_mask_returns_text_unchanged_when_no_pii_found(tmp_path: pathlib.Path):
    gateway = PiiGateway(db_path=tmp_path / "pii_map.db")

    text = "Bu cümlede hiçbir kişisel veri yok."
    assert await gateway.mask(text) == text
