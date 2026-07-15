"""aihm_karar_ara/aihm_karar_getir'in HudocClient'ı sahte (fake) bir istemciyle
çalıştığını doğrular — gerçek ağ çağrısı yapmaz."""
import pathlib

import pytest

import legalai.packages.aihm.service as service


class _FakeHudocClient:
    def __init__(self, search_results, document_text):
        self._search_results = search_results
        self._document_text = document_text

    async def search(self, **kwargs):
        return self._search_results

    async def get_document_text(self, itemid):
        return self._document_text


@pytest.fixture(autouse=True)
def _reset_client():
    service._client = None
    yield
    service._client = None


@pytest.mark.asyncio
async def test_aihm_karar_ara_maps_columns_to_summary(monkeypatch):
    fake = _FakeHudocClient(
        search_results=[
            {
                "itemid": "001-75327",
                "appno": "47533/99",
                "docname": "CASE OF ERGIN v. TURKEY (No. 6)",
                "kpdate": "2006-05-04T00:00:00",
                "article": "10;6;6-1",
                "respondent": "TUR",
                "importance": "2",
                "languageisocode": "ENG",
                "documentcollectionid": "CASELAW;JUDGMENTS;CHAMBER;ENG",
            }
        ],
        document_text="",
    )
    monkeypatch.setattr(service, "_get_client", lambda: fake)

    results = await service.aihm_karar_ara("ifade özgürlüğü", respondent="TUR", limit=5)

    assert len(results) == 1
    item = results[0]
    assert item["application_no"] == "47533/99"
    assert item["date"] == "2006-05-04"
    assert item["articles"] == ["10", "6", "6-1"]
    assert item["importance"] == 2


@pytest.mark.asyncio
async def test_aihm_karar_getir_parses_sections_and_caches(monkeypatch, tmp_path: pathlib.Path):
    fixture_path = (
        pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "aihm" / "001-75327.txt"
    )
    fake = _FakeHudocClient(
        search_results=[
            {
                "itemid": "001-75327",
                "appno": "47533/99",
                "docname": "CASE OF ERGIN v. TURKEY (No. 6)",
                "kpdate": "2006-05-04T00:00:00",
                "article": "10;6;6-1",
                "respondent": "TUR",
                "importance": "2",
                "languageisocode": "ENG",
                "documentcollectionid": "CASELAW;JUDGMENTS;CHAMBER;ENG",
            }
        ],
        document_text=fixture_path.read_text(encoding="utf-8"),
    )
    monkeypatch.setattr(service, "_get_client", lambda: fake)
    monkeypatch.setattr(service, "CACHE_DB_PATH", tmp_path / "cache.db", raising=False)
    monkeypatch.setattr(
        service, "get_cached", _passthrough_get_cached_factory(tmp_path / "cache.db")
    )
    monkeypatch.setattr(
        service, "set_cached", _passthrough_set_cached_factory(tmp_path / "cache.db")
    )

    result = await service.aihm_karar_getir("47533/99", lang="en")

    assert result["application_no"] == "47533/99"
    assert "procedure" in result["sections"]
    assert "operative" in result["sections"]


def _passthrough_get_cached_factory(db_path):
    from legalai.packages.aihm.cache import get_cached as real_get_cached

    async def _wrapped(cache_key, db_path_arg=db_path):
        return await real_get_cached(cache_key, db_path=db_path_arg)

    return _wrapped


def _passthrough_set_cached_factory(db_path):
    from legalai.packages.aihm.cache import set_cached as real_set_cached

    async def _wrapped(cache_key, payload, db_path_arg=db_path):
        return await real_set_cached(cache_key, payload, db_path=db_path_arg)

    return _wrapped
