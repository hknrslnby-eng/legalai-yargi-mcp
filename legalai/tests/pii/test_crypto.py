from legalai.packages.pii import crypto


def test_dek_roundtrip_wrap_unwrap():
    dek = crypto.generate_dek()
    wrapped = crypto.wrap_dek(dek)
    assert crypto.unwrap_dek(wrapped) == dek


def test_encrypt_decrypt_roundtrip():
    dek = crypto.generate_dek()
    ciphertext = crypto.encrypt_value("Ahmet Yılmaz", dek)
    assert ciphertext != "Ahmet Yılmaz"
    assert crypto.decrypt_value(ciphertext, dek) == "Ahmet Yılmaz"


def test_get_kek_is_stable_within_process_when_env_not_set(monkeypatch):
    from legalai.packages.shared.settings import settings

    monkeypatch.setattr(settings, "pii_kek_base64", "")
    crypto._process_kek_cache = None  # temiz başlangıç
    first = crypto.get_kek()
    second = crypto.get_kek()
    assert first == second
