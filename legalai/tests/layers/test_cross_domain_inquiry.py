from legalai.packages.layers.cross_domain_inquiry import build_cross_domain_inquiry
from legalai.packages.shared.types import Document


def test_cross_domain_inquiry_builds_positive_negative_and_cross_effects_for_each_domain():
    inquiry = build_cross_domain_inquiry(
        "Calisanin sirket verilerini rakibe aktarmasi ceza, kvkk ve sozlesme sorumlulugu dogurur mu?",
        ["ceza", "kvkk", "hukuk"],
        documents=(
            Document(id="doc-1", body="USB loglari ve disiplin tutanagi", source="internal"),
        ),
    )

    assert inquiry.detected_domains == ["ceza", "kvkk", "hukuk"]
    assert inquiry.allowed_document_ids == ["doc-1"]
    assert len(inquiry.branches) == 3
    assert all(branch.positive_effects for branch in inquiry.branches)
    assert all(branch.negative_effects for branch in inquiry.branches)
    assert all(branch.cross_domain_effects for branch in inquiry.branches)

    rendered = inquiry.render()

    assert "Cross-domain inquiry" in rendered
    assert "Positive effects" in rendered
    assert "Negative effects" in rendered
    assert "Cross-domain evidence/argument effects" in rendered
    assert "#doc-1" in rendered

