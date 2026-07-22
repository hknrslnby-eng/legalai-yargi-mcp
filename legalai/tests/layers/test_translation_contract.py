import pytest

from legalai.packages.layers.translation_contract import (
    SUPPORTED_OUTPUT_LANGUAGES,
    TranslationRequest,
    build_translation_instructions,
    extract_immutable_citation_ids,
)


def test_all_supported_legal_output_languages_validate():
    for language in SUPPORTED_OUTPUT_LANGUAGES:
        request = TranslationRequest("tr", language, "source_to_output")
        assert request.output_language == language


def test_citation_ids_are_immutable_and_certified_translation_is_not_claimed():
    request = TranslationRequest("tr", "de", "source_to_output")
    text = "ECLI:TR:ABC:2025:1 CELEX:32016R0679 Yargıtay 2024/1 E."

    assert set(extract_immutable_citation_ids(text)) >= {"ECLI:TR:ABC:2025:1", "CELEX:32016R0679"}
    instructions = build_translation_instructions(request, text)
    assert "ECLI:TR:ABC:2025:1" in instructions
    assert "sertifikalı çeviri" in instructions
    assert "sunma" in instructions


def test_unsupported_language_is_rejected():
    with pytest.raises(ValueError):
        TranslationRequest("tr", "xx", "source_to_output")
