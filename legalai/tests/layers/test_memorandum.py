import pytest

from legalai.packages.layers.memorandum import (
    MEMORANDUM_SECTIONS,
    MemorandumProfile,
    build_memorandum_instructions,
)


def test_memorandum_has_integrated_assessment_result_and_sources_sections():
    instructions = build_memorandum_instructions(
        MemorandumProfile(detail_level="exhaustive", max_source_quotes=5),
        source_ids=("d-1",),
    )

    assert len(MEMORANDUM_SECTIONS) == 13
    assert "11. Bütünleştirici Ayrıntılı Değerlendirme" in instructions
    assert "12. Sonuç" in instructions
    assert "13. Kaynakça ve İlgili Kısa Alıntılar" in instructions
    assert "#d-1" in instructions
    assert "Ham düşünce zincirini gösterme" in instructions


def test_memorandum_rejects_unknown_detail_level():
    with pytest.raises(ValueError):
        MemorandumProfile(detail_level="unlimited")
