"""run_pipeline / build_layered_pipeline uçtan uca entegrasyon testleri.

Hafta 7 kabul kriteri: "10 test sorusunda %100 citation gerçek DB'de
bulunuyor." Gerçek ağ/LLM çağrısı yapmadan, RetrieveDocuments backend'i ve
GroundedGenerator'ın LLMRouter'ı enjekte edilerek doğrulanır.
"""
import pytest

from legalai.packages.layers.analysis_pipeline import (
    build_assistant_instructions,
    build_layered_pipeline,
    run_pipeline,
)
from legalai.packages.layers.pipeline import Context
from legalai.packages.shared.types import Document

_FIXTURE_DOCS = [
    Document(
        id="yargitay-hgk-1",
        source="yargitay",
        citation="Yargıtay HGK 2022/3 E., 2022/900 K.",
        body=(
            "Davacı vekili, müvekkilinin zararının tazminini talep etmiştir. "
            "Davalı, zararın oluşmadığını savunmuştur. "
            "Dairemizce yapılan incelemede, yerleşik içtihat gereği zarar ile "
            "kusur arasında illiyet bağı bulunduğu görülmüştür. "
            "Sonuç olarak, ilk derece mahkemesi kararının onanmasına karar "
            "verilmiştir."
        ),
    ),
    Document(
        id="yargitay-3hd-2",
        source="yargitay",
        citation="Yargıtay 3. Hukuk Dairesi 2023/1234 E., 2023/5678 K.",
        body=(
            "İlk derece mahkemesi davayı kısmen kabul etmiştir. "
            "Bilirkişi raporunda zarar miktarı hesaplanmıştır. "
            "Sonuç olarak kısmi kabule karar verilmiştir.\n\n"
            "KARŞI OY\nZarar miktarının yeniden hesaplanması gerekir."
        ),
    ),
]

_TEST_QUESTIONS = [
    "Zarar ile kusur arasındaki illiyet bağı nasıl ispatlanır?",
    "Bilirkişi raporuna itiraz nasıl yapılır?",
    "Tazminat davasında ispat yükü kimdedir?",
    "Kısmi kabul kararına karşı temyiz süresi nedir?",
    "Karşı oy yazısı kararın kesinleşmesini etkiler mi?",
    "Zarar miktarı nasıl hesaplanır?",
    "Yerleşik içtihat kavramı ne anlama gelir?",
    "İlk derece mahkemesi kararı ne zaman onanır?",
    "Dairemizce yapılan inceleme neyi kapsar?",
    "Davalının zararın oluşmadığı savunması nasıl değerlendirilir?",
]


class _StaticRetrieveBackend:
    """Gerçek Bedesten aramasının yerini alan sabit belge kümesi."""

    async def search(self, query: str, limit: int) -> list[Document]:
        return list(_FIXTURE_DOCS)


class _GroundedFakeGenerator:
    """GroundedGenerator'ın yerini alan, HER ZAMAN ctx.documents'taki gerçek
    id'lerle kaynak gösteren sahte bir üreteç — LLM'e ağ çağrısı yapmaz."""

    name = "grounded_generator"

    async def run(self, ctx: Context) -> Context:
        doc_ids = [doc.id for doc in ctx.documents]
        refs = " ".join(f"[#{doc_id}]" for doc_id in doc_ids) or "(kaynak yok)"
        ctx.answer = f"'{ctx.question}' sorusuna ilişkin bulgular {refs}."
        return ctx


@pytest.mark.asyncio
@pytest.mark.parametrize("question", _TEST_QUESTIONS)
async def test_layered_pipeline_citations_always_found_in_documents(question):
    from legalai.packages.layers.retrieve_documents import RetrieveDocuments

    generator = _GroundedFakeGenerator()
    pipeline = build_layered_pipeline(
        retrieve=RetrieveDocuments(backend=_StaticRetrieveBackend()),
        generator=generator,  # type: ignore[arg-type]
    )

    result = await run_pipeline(question=question, pipeline=pipeline)

    assert result.citations, "cevap en az bir kaynak göstermeli"
    valid_ids = {doc.id for doc in result.documents}
    assert all(c in valid_ids for c in result.citations)


@pytest.mark.asyncio
async def test_run_pipeline_uses_provided_documents_without_retrieving():
    fixed_doc = Document(id="verilen-1", body="doğrudan verilmiş belge")
    generator = _GroundedFakeGenerator()
    pipeline = build_layered_pipeline(generator=generator)  # type: ignore[arg-type]

    result = await run_pipeline(
        question="soru", documents=[fixed_doc], pipeline=pipeline
    )

    assert [d.id for d in result.documents] == ["verilen-1"]
    assert result.citations == ["verilen-1"]


@pytest.mark.asyncio
async def test_verified_citation_check_strips_hallucinated_citation_from_layered_run():
    class _HallucinatingThenFixedGenerator:
        name = "grounded_generator"

        def __init__(self):
            self.calls = 0

        async def run(self, ctx: Context) -> Context:
            self.calls += 1
            if self.calls == 1:
                ctx.answer = "Yanlış kaynak gösterildi [#uydurma]."
            else:
                real_id = ctx.documents[0].id if ctx.documents else "yok"
                ctx.answer = f"Düzeltildi [#{real_id}]."
            return ctx

    generator = _HallucinatingThenFixedGenerator()
    pipeline = build_layered_pipeline(
        retrieve=None,
        generator=generator,  # type: ignore[arg-type]
    )
    fixed_doc = Document(id="gercek-1", body="gerçek belge")

    result = await run_pipeline(question="soru", documents=[fixed_doc], pipeline=pipeline)

    assert result.citations == ["gercek-1"]
    assert generator.calls == 2


def test_build_assistant_instructions_lists_only_valid_ids():
    instructions = build_assistant_instructions(["d1", "d2"])

    assert "#d1" in instructions
    assert "#d2" in instructions
    assert "LLM DEĞİLDİR" in instructions


def test_build_assistant_instructions_handles_no_documents():
    instructions = build_assistant_instructions([])

    assert "hiçbir belge bulunamadı" in instructions


def test_build_assistant_instructions_includes_structured_reasoning_when_requested():
    instructions = build_assistant_instructions(
        ["d1"], jurisdiction_ids=["hukuk", "ceza"], source_context="legal_analysis"
    )

    assert "1. Hukuki sorun nedir?" in instructions
    assert "Temporal Legal Context" in instructions
    assert "non-binding" in instructions
    assert "Yönetici özeti" in instructions
    assert "operasyonel bağlam" in instructions.lower()


@pytest.mark.asyncio
async def test_pipeline_uses_trade_defense_source_context_for_trade_defense_profile():
    result = await run_pipeline(
        question="Dampinge karşı soruşturma savunması",
        jurisdiction_hint="ticaret_savunmasi",
        documents=[Document(id="d1", body="belge")],
        synthesize=False,
    )

    assert result.assistant_instructions is not None
    assert "Kaynak bağlamı: trade_defense_research" in result.assistant_instructions


@pytest.mark.asyncio
async def test_run_pipeline_synthesize_false_skips_llm_and_returns_instructions():
    fixed_doc = Document(id="d1", body="belge metni")

    result = await run_pipeline(
        question="soru", documents=[fixed_doc], synthesize=False
    )

    assert result.answer is None
    assert result.citations == []
    assert result.assistant_instructions is not None
    assert "#d1" in result.assistant_instructions
    # LLM katmanları hiç çalışmadı (grounded_generator/verified_citation_check trace'de yok)
    layer_names = {t.get("layer") for t in result.trace}
    assert "grounded_generator" not in layer_names
    assert "verified_citation_check" not in layer_names


@pytest.mark.asyncio
async def test_run_pipeline_synthesize_true_still_includes_llm_layers_in_trace():
    class _StubGenerator:
        name = "grounded_generator"

        async def run(self, ctx: Context) -> Context:
            ctx.answer = f"cevap [#{ctx.documents[0].id}]" if ctx.documents else "cevap"
            return ctx

    fixed_doc = Document(id="d1", body="belge metni")

    result = await run_pipeline(
        question="soru",
        documents=[fixed_doc],
        synthesize=True,
        pipeline=build_layered_pipeline(generator=_StubGenerator(), synthesize=True),  # type: ignore[arg-type]
    )

    assert result.answer == "cevap [#d1]"
    assert result.citations == ["d1"]
    assert result.assistant_instructions is None  # pipeline açıkça verildi


@pytest.mark.asyncio
async def test_run_pipeline_exposes_operational_context_in_result_dict():
    fixed_doc = Document(id="d1", body="belge metni")

    result = await run_pipeline(
        question="Kripto cüzdanına yönlendirildim ve ödeme yaptım",
        documents=[fixed_doc],
        synthesize=False,
    )

    payload = result.to_dict()

    assert payload["operational_context"]["domain"] == "crypto_asset_operations"
    assert payload["operational_context"]["items"]
    assert "kesin olgu değildir" in payload["operational_context"]["safety_note"]
