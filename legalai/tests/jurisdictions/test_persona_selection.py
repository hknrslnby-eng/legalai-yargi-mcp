from legalai.packages.jurisdictions.selection import guess_jurisdictions


def test_guess_jurisdictions_detects_hukuk_and_ceza():
    selection = guess_jurisdictions("Sözleşme alacağı için sahte belge düzenlenmiş olabilir mi?")

    assert selection.primary in {"hukuk", "ceza"}
    assert {"hukuk", "ceza"}.issubset({selection.primary, *selection.supporting})


def test_unknown_question_uses_diger_without_losing_confidence_metadata():
    selection = guess_jurisdictions("Bu olayın hukuki çözümünü araştır.")

    assert selection.primary == "diger"
    assert 0.0 <= selection.confidence <= 1.0


def test_specialized_lens_is_returned_for_contract_question():
    selection = guess_jurisdictions("Sözleşmenin feshi ve cezai şart uygulanır mı?")

    assert "sozlesmeler" in selection.expert_lenses
