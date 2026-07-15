"""Zarf şifreleme (envelope encryption) — bkz. FORK-KAPSAMLI-PLAN.md §7
("PII mapping ... mapping değeri her tenant KEK ile şifreli").

Şema: her tenant için rastgele bir DEK (Data Encryption Key) üretilir;
gerçek PII değerleri DEK ile şifrelenir. DEK'in kendisi, `.env`'deki sabit
KEK (Key Encryption Key) ile şifrelenip SQLite'ta saklanır. KEK asla
kod içine yazılmaz; `settings.pii_kek_base64` üstünden gelir.

Üretimde `pii_kek_base64` boş bırakılmamalı: boşsa süreç her başlatıldığında
rastgele (ve tutarsız) bir KEK üretilir, önceki oturumlarda maskelenmiş
veriler bir daha AÇILAMAZ (unmask edilemez). Bu, bilinçli bir "önce
güvenli tarafta hata yap" tasarımıdır.
"""
from __future__ import annotations

import logging

from cryptography.fernet import Fernet

from legalai.packages.shared.settings import settings

logger = logging.getLogger(__name__)

_process_kek_cache: bytes | None = None


def get_kek() -> bytes:
    """Süreç içinde tutarlı bir KEK döner.

    `.env`'de `PII_KEK_BASE64` ayarlıysa onu kullanır (kalıcı, tavsiye
    edilen); yoksa bu süreç ömrü boyunca sabit kalan rastgele bir KEK
    üretir ve loglar bir uyarı basar.
    """
    global _process_kek_cache
    if settings.pii_kek_base64:
        return settings.pii_kek_base64.encode("utf-8")
    if _process_kek_cache is None:
        logger.warning(
            "PII_KEK_BASE64 .env'de ayarlı değil — bu süreç ömrü boyunca geçerli "
            "rastgele bir KEK üretildi. Süreç yeniden başladığında ÖNCEKİ "
            "maskelenmiş veriler açılamaz. Üretimde bu değeri sabitleyin: "
            "python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
        _process_kek_cache = Fernet.generate_key()
    return _process_kek_cache


def generate_dek() -> bytes:
    return Fernet.generate_key()


def wrap_dek(dek: bytes, kek: bytes | None = None) -> str:
    """DEK'i KEK ile şifreler; SQLite'ta saklanabilir bir string döner."""
    f = Fernet(kek or get_kek())
    return f.encrypt(dek).decode("utf-8")


def unwrap_dek(wrapped_dek: str, kek: bytes | None = None) -> bytes:
    f = Fernet(kek or get_kek())
    return f.decrypt(wrapped_dek.encode("utf-8"))


def encrypt_value(plaintext: str, dek: bytes) -> str:
    return Fernet(dek).encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_value(ciphertext: str, dek: bytes) -> str:
    return Fernet(dek).decrypt(ciphertext.encode("utf-8")).decode("utf-8")
