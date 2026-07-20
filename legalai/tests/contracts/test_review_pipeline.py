from __future__ import annotations

from types import SimpleNamespace

import pytest

from legalai.packages.contracts.models import ContractReviewRequest
from legalai.packages.contracts.review import review_contract


def request_for(text: str, *, detail_level: str = "standard") -> ContractReviewRequest:
    return ContractReviewRequest(
        contract_text=text,
        file_path=None,
        purpose="risk review",
        position="buyer",
        detail_level=detail_level,
        event_dates=["2026-07-20"],
        jurisdiction_hint="hukuk",
        server_side_synthesis=False,
    )


def fake_analysis():
    return SimpleNamespace(
        to_dict=lambda: {
            "sources": [{"doc_id": "d-1", "citation": "Synthetic source", "source": "local"}],
            "temporal_context": {"status": "available"},
            "operational_context": {"domain": None},
            "assistant_instructions": "Use only returned sources.",
        }
    )


@pytest.mark.asyncio
async def test_review_queries_sources_with_redacted_text_only():
    seen: list[str] = []

    async def fake_pipeline(question: str, **kwargs):
        seen.append(question)
        return fake_analysis()

    result = await review_contract(
        request_for("Taraf: Ayşe Yılmaz, TCKN 12345678901\nMADDE 1 - Bedel"),
        pipeline_runner=fake_pipeline,
    )

    assert "12345678901" not in seen[0]
    assert "Ayşe Yılmaz" not in seen[0]
    assert result.evidence[0]["doc_id"] == "d-1"
    assert result.privacy["persisted"] is False


@pytest.mark.asyncio
async def test_foreign_contract_requests_bilingual_revision():
    async def fake_pipeline(question: str, **kwargs):
        return fake_analysis()

    result = await review_contract(
        request_for("ARTICLE 4 - Governing law: English law; arbitration in Paris"),
        pipeline_runner=fake_pipeline,
    )

    assert "source_language_revision" in result.assistant_instructions
    assert "Turkish counterpart" in result.assistant_instructions
    assert result.classification["foreign_law_layer"] == "mohuk_priority"
    assert result.non_binding is True
