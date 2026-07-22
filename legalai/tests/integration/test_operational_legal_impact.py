import pytest

from legalai.packages.layers.analysis_pipeline import run_pipeline
from legalai.packages.layers.pipeline import Context, Pipeline


class _SetQuestionContext:
    name = "fixture"

    async def run(self, ctx: Context) -> Context:
        ctx.jurisdiction_id = "ceza"
        ctx.jurisdiction_ids = ["ceza"]
        return ctx


@pytest.mark.asyncio
async def test_analysis_output_keeps_operational_layer_and_legal_reasoning_context():
    result = await run_pipeline(
        "IBAN ve kripto transfer zincirinde failin rolü",
        pipeline=Pipeline([_SetQuestionContext()]),
        synthesize=False,
    )

    payload = result.to_dict()
    assert payload["operational_context"]["findings"]
    assert any(item["legal_impacts"] for item in payload["operational_context"]["findings"])
    assert payload["analysis_only"] is True
