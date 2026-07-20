from legalai.packages.layers.authority_gap import (
    assess_authority_gap,
    build_authority_gap_instructions,
)
from legalai.packages.shared.types import Document


def test_authority_gap_does_not_present_retrieved_documents_as_direct_authority():
    result = assess_authority_gap(
        [Document(id="d1", source="yargitay", citation="Yargıtay HGK 2020/1 E.", body="metin")],
        ["hukuk"],
    )

    assert result.direct_authority_status == "direct_applicability_not_established"
    assert result.candidate_source_ids == ("d1",)
    assert result.to_dict()["non_binding"] is True


def test_authority_gap_instructions_include_no_authority_and_legality_limits():
    instructions = build_authority_gap_instructions(["d1"], ["ceza", "vergi"])

    assert "doğrudan" in instructions.lower()
    assert "emsal" in instructions
    assert "kanunilik" in instructions
    assert "#d1" in instructions
