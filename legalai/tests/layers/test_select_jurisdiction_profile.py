import pytest

from legalai.packages.layers.pipeline import Context
from legalai.packages.layers.select_jurisdiction_profile import SelectJurisdictionProfile


@pytest.mark.asyncio
async def test_select_jurisdiction_profile_keeps_valid_id():
    ctx = Context(tenant_id="test", question="q", mode="standard", jurisdiction_id="ceza")

    result = await SelectJurisdictionProfile().run(ctx)

    assert result.jurisdiction_id == "ceza"


@pytest.mark.asyncio
async def test_select_jurisdiction_profile_falls_back_to_hukuk_when_missing():
    ctx = Context(tenant_id="test", question="q", mode="standard", jurisdiction_id=None)

    result = await SelectJurisdictionProfile().run(ctx)

    assert result.jurisdiction_id == "hukuk"


@pytest.mark.asyncio
async def test_select_jurisdiction_profile_falls_back_when_unknown_id():
    ctx = Context(tenant_id="test", question="q", mode="standard", jurisdiction_id="olmayan_tur")

    result = await SelectJurisdictionProfile().run(ctx)

    assert result.jurisdiction_id == "hukuk"
