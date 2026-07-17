"""Regex tabanlı PII (kişisel veri) dedektörleri — Hafta 6 aşama 1.

Bu modül SADECE örüntüyle (pattern) yakalanabilen, yapılandırılmış
tanımlayıcıları bulur: TCKN, telefon, e-posta, IBAN, plaka. İsim/kurum
(PERSON/ORG) gibi serbest metin varlıkları için NER modeli gerekir — bu,
`HUGGINGFACE_TOKEN` alındığında eklenecek ayrı bir katmandır (bkz.
FORK-KAPSAMLI-PLAN.md §Hafta 6, 15 Temmuz 2026 eki: "önce regex, sonra NER").

Her dedektör `(etiket, başlangıç, bitiş, orijinal_metin)` demetleri döner;
`merger.py` bunları çakışmasız aralıklara indirger.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

TCKN_RE = re.compile(r"(?<!\d)\d{11}(?!\d)")
PHONE_RE = re.compile(r"(?<!\d)(?:0)?5\d{2}[\s.\-]?\d{3}[\s.\-]?\d{2}[\s.\-]?\d{2}(?!\d)")
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
IBAN_RE = re.compile(r"\bTR\d{2}[\s]?(?:\d{4}[\s]?){5}\d{2}\b", re.IGNORECASE)
PLAKA_RE = re.compile(r"\b\d{2}\s?[A-PR-VYZ]{1,3}\s?\d{2,4}\b")
_NAME_WORD = r"[A-ZÇĞİÖŞÜ][a-zçğıöşü]+"
CONTEXT_NAME_RE = re.compile(
    rf"\b(?:ad\s*soyad|isim|müvekkil|davacı|davalı|sanık|mağdur|başvurucu)\s*[:\-]\s*"
    rf"(?P<value>{_NAME_WORD}(?:\s+{_NAME_WORD}){{1,3}})",
    re.IGNORECASE,
)
ADDRESS_RE = re.compile(r"(?i)\b(?:adres|ikamet adresi)\s*[:\-]\s*(?P<value>[^\n.;]+)")
BIRTH_DATE_RE = re.compile(
    r"(?i)\bdoğum\s+tarihi\s*[:\-]\s*(?P<value>\d{1,2}[./]\d{1,2}[./]\d{4})"
)
PERSON_NAME_RE = re.compile(
    rf"(?<![\w])(?P<value>{_NAME_WORD}(?:\s+{_NAME_WORD}){{1,2}})(?![\w])"
)
_COMMON_CAPITALIZED_PHRASES = {
    "Ad Soyad",
    "Anayasa Mahkemesi",
    "Türk Borçlar",
    "Avukatlık Kanunu",
    "Tüketici Mahkemesi",
    "İdare Mahkemesi",
    "Yargıtay Hukuk",
    "Yargıtay Ceza",
}


@dataclass(frozen=True)
class Match:
    label: str
    start: int
    end: int
    text: str


def _luhn_free_tckn_checksum(digits: str) -> bool:
    """Türkiye Cumhuriyeti Kimlik Numarası algoritmik doğrulaması.

    Kural: ilk hane 0 olamaz. d10 = ((d1+d3+d5+d7+d9)*7 - (d2+d4+d6+d8)) mod 10.
    d11 = (d1+...+d10) mod 10.
    """
    if len(digits) != 11 or digits[0] == "0":
        return False
    d = [int(c) for c in digits]
    odd_sum = d[0] + d[2] + d[4] + d[6] + d[8]
    even_sum = d[1] + d[3] + d[5] + d[7]
    d10 = ((odd_sum * 7) - even_sum) % 10
    d11 = (sum(d[:10])) % 10
    return d10 == d[9] and d11 == d[10]


def _iban_mod97_valid(iban_raw: str) -> bool:
    iban = iban_raw.replace(" ", "").upper()
    if len(iban) != 26 or not iban.startswith("TR"):
        return False
    rearranged = iban[4:] + iban[:4]
    numeric = "".join(str(int(ch, 36)) if ch.isalpha() else ch for ch in rearranged)
    try:
        return int(numeric) % 97 == 1
    except ValueError:
        return False


def find_tckn(text: str) -> list[Match]:
    matches = []
    for m in TCKN_RE.finditer(text):
        if _luhn_free_tckn_checksum(m.group()):
            matches.append(Match("TCKN", m.start(), m.end(), m.group()))
    return matches


def find_phone(text: str) -> list[Match]:
    return [Match("TELEFON", m.start(), m.end(), m.group()) for m in PHONE_RE.finditer(text)]


def find_email(text: str) -> list[Match]:
    return [Match("EPOSTA", m.start(), m.end(), m.group()) for m in EMAIL_RE.finditer(text)]


def find_iban(text: str) -> list[Match]:
    matches = []
    for m in IBAN_RE.finditer(text):
        if _iban_mod97_valid(m.group()):
            matches.append(Match("IBAN", m.start(), m.end(), m.group()))
    return matches


def find_plaka(text: str) -> list[Match]:
    return [Match("PLAKA", m.start(), m.end(), m.group()) for m in PLAKA_RE.finditer(text)]


def find_contextual(text: str) -> list[Match]:
    matches: list[Match] = []
    for pattern, label in (
        (CONTEXT_NAME_RE, "KISI"),
        (ADDRESS_RE, "ADRES"),
        (BIRTH_DATE_RE, "DOGUM_TARIHI"),
    ):
        for match in pattern.finditer(text):
            value = match.group("value")
            start = match.start("value")
            matches.append(Match(label, start, match.end("value"), value))
    return matches


def find_probable_person_names(text: str) -> list[Match]:
    matches: list[Match] = []
    for match in PERSON_NAME_RE.finditer(text):
        value = match.group("value")
        if value in _COMMON_CAPITALIZED_PHRASES:
            continue
        prefix = text[max(0, match.start() - 24) : match.start()].casefold()
        if any(label in prefix for label in ("ad soyad", "isim", "müvekkil", "davacı", "davalı", "sanık", "mağdur", "başvurucu", "adres")):
            continue
        matches.append(Match("KISI", match.start("value"), match.end("value"), value))
    return matches


def find_all(text: str) -> list[Match]:
    """Tüm regex dedektörlerini çalıştırır; sonuçlar örtüşebilir, sıralama
    yapılmaz — `merger.merge_matches()` bunu çakışmasız hale getirir."""
    return [
        *find_contextual(text),
        *find_tckn(text),
        *find_phone(text),
        *find_email(text),
        *find_iban(text),
        *find_plaka(text),
        *find_probable_person_names(text),
    ]
