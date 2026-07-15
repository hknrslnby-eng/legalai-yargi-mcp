import pytest

from legalai.packages.layers.pipeline import Context, Pipeline


class _UppercaseLayer:
    name = "uppercase"

    async def run(self, ctx: Context) -> Context:
        ctx.answer = (ctx.answer or "").upper()
        return ctx


class _AppendLayer:
    name = "append"

    async def run(self, ctx: Context) -> Context:
        ctx.answer = f"{ctx.answer}!"
        return ctx


@pytest.mark.asyncio
async def test_pipeline_runs_layers_in_order():
    ctx = Context(tenant_id="test", question="soru", mode="standard", answer="merhaba")
    pipeline = Pipeline(layers=[_UppercaseLayer(), _AppendLayer()])

    result = await pipeline.run(ctx)

    assert result.answer == "MERHABA!"


@pytest.mark.asyncio
async def test_pipeline_records_trace_for_each_layer():
    ctx = Context(tenant_id="test", question="soru", mode="standard", answer="x")
    pipeline = Pipeline(layers=[_UppercaseLayer(), _AppendLayer()])

    result = await pipeline.run(ctx)

    assert [t["layer"] for t in result.trace] == ["uppercase", "append"]
    assert all(isinstance(t["ms"], float) for t in result.trace)
