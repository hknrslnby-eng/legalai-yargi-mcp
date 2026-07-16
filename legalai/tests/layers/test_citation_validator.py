from legalai.packages.layers.citation_validator import validate_citations


def test_validate_citations_returns_valid_when_all_ids_known():
    result = validate_citations("İddia [#d1] ve [#d2].", known_doc_ids=["d1", "d2", "d3"])

    assert result.valid is True
    assert result.citations == ["d1", "d2"]
    assert result.invalid_citations == []


def test_validate_citations_flags_unknown_ids():
    result = validate_citations("Uydurma kaynak [#hayali].", known_doc_ids=["d1"])

    assert result.valid is False
    assert result.invalid_citations == ["hayali"]


def test_validate_citations_handles_no_citations():
    result = validate_citations("Kaynak göstermeyen bir cevap.", known_doc_ids=["d1"])

    assert result.valid is True
    assert result.citations == []


def test_validate_citations_to_dict_shape():
    result = validate_citations("[#d1]", known_doc_ids=["d1"])

    assert result.to_dict() == {"citations": ["d1"], "invalid_citations": [], "valid": True}
