from legalai.packages.pii.patterns import find_all, find_email, find_iban, find_phone, find_plaka, find_tckn

VALID_TCKN = "10000000146"
VALID_IBAN = "TR330006100519786457841326"


def test_find_tckn_accepts_algorithmically_valid_number():
    matches = find_tckn(f"Müşteri TCKN: {VALID_TCKN} numaralı kişidir.")
    assert len(matches) == 1
    assert matches[0].text == VALID_TCKN
    assert matches[0].label == "TCKN"


def test_find_tckn_rejects_invalid_checksum():
    # 11 rakam ama checksum tutmuyor
    matches = find_tckn("Sipariş numarası 12345678901 idi.")
    assert matches == []


def test_find_phone_matches_common_formats():
    assert len(find_phone("Beni 0532 123 45 67 numaralı telefondan arayın.")) == 1
    assert len(find_phone("Cep: 532-123-45-67")) == 1


def test_find_email_matches_standard_address():
    matches = find_email("İletişim: ahmet.yilmaz@ornek.com.tr adresinden yapılabilir.")
    assert len(matches) == 1
    assert matches[0].text == "ahmet.yilmaz@ornek.com.tr"


def test_find_iban_accepts_mod97_valid_iban():
    matches = find_iban(f"Hesap: {VALID_IBAN}")
    assert len(matches) == 1


def test_find_iban_rejects_invalid_checksum():
    matches = find_iban("Hesap: TR330006100519786457841300")
    assert matches == []


def test_find_plaka_matches_turkish_plate_format():
    matches = find_plaka("Araç plakası 34 ABC 1234 olarak tespit edildi.")
    assert len(matches) == 1


def test_find_all_combines_all_detectors():
    text = f"TCKN {VALID_TCKN}, IBAN {VALID_IBAN}, tel 0532 123 45 67"
    labels = {m.label for m in find_all(text)}
    assert labels == {"TCKN", "IBAN", "TELEFON"}
