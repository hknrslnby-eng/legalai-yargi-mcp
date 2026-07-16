"""VerifiedCitationCheck'in uydurma [#doc_id] referanslarını yakalayıp
GroundedGenerator'ı tekrar çağırdığını (max_retries ile sınırlı) doğrular.
Hafta 7 kabul kriteri: "10 test sorusunda %100 citation gerçek DB'de
bulunuyor" — bu testler o davranışın birim testleridir."""
import pytest

from legalai.packages.layers.pipeline import Context
from legalai.packages.layers.verified_citation_check import (
    VerifiedCitationCheck,
    extract_citations,
)
from legalai.packages.shared.types import Document


def test_extract_citations_deduplicates_and_preserves_order():
    answer = "İlk iddia [#d1]. İkinci iddia [#d2]. Tekrar [#d1]."
    assert extract_citations(answer) == ["d1", "d2"]


def test_extract_citations_returns_empty_list_for_none():
    assert extract_citations(None) == []


class _ScriptedGenerator:
    """Her çağrıda listede sıradaki cevabı döner; sınırı aşan çağrı hata verir."""

    name = "grounded_generator"

    def __init__(self, answers: list[str]):
        self._answers = list(answers)
        self.call_count = 0

    async def run(self, ctx: Context) -> Context:
        self.call_count += 1
        ctx.answer = self._answers.pop(0)
        return ctx


@pytest.mark.asyncio
async def test_verified_citation_check_accepts_valid_citations_without_retry():
    generator = _ScriptedGenerator(["ilk cevap"])  # kullanılmayacak
    doc = Document(id="d1", body="")
    ctx = Context(
        tenant_id="test", question="q", mode="layered", documents=[doc], answer="Cevap [#d1]."
    )

    result = await VerifiedCitationCheck(generator=generator, max_retries=2).run(ctx)

    assert result.citations == ["d1"]
    assert generator.call_count == 0  # geçerliydi, tekrar denemeye gerek yoktu


@pytest.mark.asyncio
async def test_verified_citation_check_retries_on_invalid_citation_then_succeeds():
    generator = _ScriptedGenerator(["Düzeltilmiş cevap [#d1]."])
    doc = Document(id="d1", body="")
    ctx = Context(
        tenant_id="test",
        question="q",
        mode="layered",
        documents=[doc],
        answer="Uydurma referans [#uydurma-id].",
    )

    result = await VerifiedCitationCheck(generator=generator, max_retries=2).run(ctx)

    assert result.citations == ["d1"]
    assert generator.call_count == 1
    assert any(t.get("gave_up") for t in result.trace) is False


@pytest.mark.asyncio
async def test_verified_citation_check_gives_up_after_max_retries():
    generator = _ScriptedGenerator(
        ["Hâlâ uydurma [#hayali-1].", "Yine uydurma [#hayali-2]."]
    )
    doc = Document(id="d1", body="")
    ctx = Context(
        tenant_id="test",
        question="q",
        mode="layered",
        documents=[doc],
        answer="Baştan uydurma [#hayali-0].",
    )

    result = await VerifiedCitationCheck(generator=generator, max_retries=2).run(ctx)

    assert result.citations == []  # tüm referanslar geçersizdi
    assert generator.call_count == 2
    assert any(t.get("gave_up") for t in result.trace)


@pytest.mark.asyncio
async def test_verified_citation_check_skips_retry_when_llm_not_configured():
    generator = _ScriptedGenerator([])  # çağrılmamalı
    ctx = Context(tenant_id="test", question="q", mode="layered", answer=None)

    result = await VerifiedCitationCheck(generator=generator).run(ctx)

    assert result.citations == []
    assert generator.call_count == 0
