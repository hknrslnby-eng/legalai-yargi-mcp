import pytest

import legalai.packages.aihm.aym_bridge as bridge


def test_extract_applicant_name_matches_standard_title():
    assert bridge.extract_applicant_name("HASAN DURMUŞ Başvurusuna İlişkin Karar") == "HASAN DURMUŞ"


def test_extract_applicant_name_returns_none_for_unsupported_title():
    assert bridge.extract_applicant_name("2023/1234 Esas Sayılı Kararın Düzeltilmesi") is None


def test_extract_decision_year_parses_turkish_date_format():
    assert bridge.extract_decision_year("15/03/2021") == 2021


def test_extract_decision_year_returns_none_for_malformed_date():
    assert bridge.extract_decision_year("not-a-date") is None


class _FakeAymDecision:
    def __init__(self, title, decision_reference_no, decision_date_summary):
        self.title = title
        self.decision_reference_no = decision_reference_no
        self.decision_date_summary = decision_date_summary
        self.decision_making_body = "Birinci Bölüm"


class _FakeAymSearchResult:
    def __init__(self, decisions):
        self.decisions = decisions


class _FakeAymClient:
    def __init__(self, decisions):
        self._decisions = decisions
        self.closed = False

    async def search_bireysel_basvuru_report(self, params):
        return _FakeAymSearchResult(self._decisions)

    async def close_client_session(self):
        self.closed = True


class _FakeHudocClient:
    def __init__(self, results):
        self._results = results

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        return None

    async def search(self, **kwargs):
        return self._results


@pytest.mark.asyncio
async def test_aihm_aym_kopru_returns_no_match_when_basvuru_no_not_found(monkeypatch):
    monkeypatch.setattr(
        bridge,
        "AnayasaBireyselBasvuruApiClient",
        lambda: _FakeAymClient(decisions=[]),
    )

    result = await bridge.aihm_aym_kopru("2099/99999")

    assert result["found"] is False
    assert result["candidates"] == []


@pytest.mark.asyncio
async def test_aihm_aym_kopru_finds_candidate_via_name_matching(monkeypatch):
    fake_aym = _FakeAymClient(
        decisions=[
            _FakeAymDecision(
                title="YÜKSEL YALÇINKAYA Başvurusuna İlişkin Karar",
                decision_reference_no="2019/50172",
                decision_date_summary="26/09/2023",
            )
        ]
    )
    monkeypatch.setattr(bridge, "AnayasaBireyselBasvuruApiClient", lambda: fake_aym)

    fake_hudoc = _FakeHudocClient(
        results=[
            {
                "appno": "15669/20",
                "docname": "CASE OF YÜKSEL YALÇINKAYA v. TÜRKİYE",
                "kpdate": "2023-09-26T00:00:00",
            },
            {
                "appno": "1111/11",
                "docname": "CASE OF SOMEONE ELSE v. TÜRKİYE",
                "kpdate": "2023-01-01T00:00:00",
            },
        ]
    )
    monkeypatch.setattr(bridge, "HudocClient", lambda: fake_hudoc)

    result = await bridge.aihm_aym_kopru("2019/50172")

    assert result["found"] is True
    assert result["applicant_name_used_for_search"] == "YÜKSEL YALÇINKAYA"
    assert len(result["candidates"]) == 1
    assert result["candidates"][0]["application_no"] == "15669/20"


@pytest.mark.asyncio
async def test_aihm_aym_kopru_reports_unparseable_title(monkeypatch):
    fake_aym = _FakeAymClient(
        decisions=[
            _FakeAymDecision(
                title="Kurumsal Başvuru Kararı",
                decision_reference_no="2020/1",
                decision_date_summary="01/01/2020",
            )
        ]
    )
    monkeypatch.setattr(bridge, "AnayasaBireyselBasvuruApiClient", lambda: fake_aym)

    result = await bridge.aihm_aym_kopru("2020/1")

    assert result["found"] is True
    assert result["candidates"] == []
    assert "otomatik çıkarılamadı" in result["reason"]
