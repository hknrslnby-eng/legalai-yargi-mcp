"""FORK-KAPSAMLI-PLAN.md §10 Hafta 3 kabul kriteri:
'vekalet ücreti nasıl hesaplanır?' sorulduğunda hukuk profilinin
seçilmesi gerekir."""
import pytest

from legalai.packages.layers.pipeline import Context, Pipeline
from legalai.packages.layers.qualify_issue import QualifyIssue
from legalai.packages.layers.select_jurisdiction_profile import SelectJurisdictionProfile


@pytest.mark.asyncio
async def test_vekalet_ucreti_sorusu_hukuk_profiline_yonlenir():
    ctx = Context(tenant_id="test", question="vekalet ücreti nasıl hesaplanır?", mode="standard")
    pipeline = Pipeline(layers=[QualifyIssue(), SelectJurisdictionProfile()])

    result = await pipeline.run(ctx)

    assert result.jurisdiction_id == "hukuk"
