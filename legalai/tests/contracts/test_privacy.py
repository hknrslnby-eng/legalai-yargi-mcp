from __future__ import annotations

from legalai.packages.contracts import ContractPrivacyGate


def test_contract_redaction_never_persists_direct_identifiers():
    result = ContractPrivacyGate().redact("PARTY_NAME, TCKN 12345678901, TR1200010000")

    assert "12345678901" not in result.text
    assert "TR1200010000" not in result.text
    assert result.persisted is False


def test_contract_redaction_masks_party_address_and_signature_lines():
    raw = (
        "Taraf: Ayşe Yılmaz\n"
        "Adres: İstiklal Caddesi No: 10 Beyoğlu/İstanbul\n"
        "İmza: Ayşe Yılmaz\n"
        "E-posta: ayse@example.com\n"
        "Telefon: +90 555 123 45 67"
    )

    result = ContractPrivacyGate().redact(raw)

    assert "Ayşe Yılmaz" not in result.text
    assert "İstiklal Caddesi" not in result.text
    assert "ayse@example.com" not in result.text
    assert "555 123 45 67" not in result.text
    assert result.persisted is False
