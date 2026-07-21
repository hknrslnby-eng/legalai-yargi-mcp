from legalai.packages.layers.operational_cards import build_operational_cards


_ALLOWED_LABELS = {
    "operasyonel hipotez",
    "kullanıcı beyanı",
    "belgeyle desteklenen olgu",
    "doğrulama gerekli",
}

_REQUIRED_CATEGORIES = {
    "actors",
    "workflow",
    "incentives",
    "technical_traces",
    "unlawful_patterns",
    "alternative_explanations",
}


def test_build_operational_cards_covers_crypto_iban_fraud_without_treating_inference_as_fact():
    cards = build_operational_cards(
        "Kripto yatırım vaadiyle IBAN'a para gönderdim, sonra cüzdana yönlendirildim.",
        ["ceza"],
        supplied_facts=("İki farklı IBAN ve bir kripto cüzdan adresi paylaşıldı.",),
    )

    assert {card.category for card in cards} == _REQUIRED_CATEGORIES
    assert {card.label for card in cards} <= _ALLOWED_LABELS
    assert any(card.label == "kullanıcı beyanı" for card in cards)
    assert any(card.label == "operasyonel hipotez" for card in cards)
    assert any("iban" in card.text.casefold() for card in cards)
    assert any("cüzdan" in card.text.casefold() for card in cards)
    assert all("kesinleşmiştir" not in card.text.casefold() for card in cards)


def test_build_operational_cards_covers_contract_and_market_operations():
    cards = build_operational_cards(
        "Dağıtım sözleşmesi, bayi fiyatları ve pazar uygulamaları hakkında risk analizi istiyorum.",
        ["rekabet", "hukuk"],
    )

    assert {card.category for card in cards} == _REQUIRED_CATEGORIES
    assert {card.label for card in cards} <= _ALLOWED_LABELS
    assert any("dağıtım" in card.text.casefold() for card in cards)
    assert any("pazar" in card.text.casefold() for card in cards)
    assert any(card.label == "doğrulama gerekli" for card in cards)


def test_build_operational_cards_covers_technical_report_context():
    cards = build_operational_cards(
        "Bilirkişi teknik raporunda log kayıtları, sunucu kesintisi ve zaman damgaları tartışılıyor.",
        ["hukuk"],
        supplied_facts=("Teknik raporda hata zaman çizelgesi tablo halinde yer alıyor.",),
    )

    assert {card.category for card in cards} == _REQUIRED_CATEGORIES
    assert {card.label for card in cards} <= _ALLOWED_LABELS
    technical = [card for card in cards if card.category == "technical_traces"]
    assert technical
    assert any("log" in card.text.casefold() or "zaman" in card.text.casefold() for card in technical)
    assert any(card.label == "belgeyle desteklenen olgu" for card in cards)


def test_build_operational_cards_handles_unknown_context_cautiously():
    cards = build_operational_cards("Bir olay yaşadım, neye bakmalıyım?", [])

    assert {card.category for card in cards} == _REQUIRED_CATEGORIES
    assert {card.label for card in cards} <= _ALLOWED_LABELS
    assert any(card.label == "doğrulama gerekli" for card in cards)
    assert all(card.label != "belgeyle desteklenen olgu" for card in cards)
    assert any("alternatif" in card.text.casefold() for card in cards)
