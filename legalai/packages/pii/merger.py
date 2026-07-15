"""Çakışan PII eşleşmelerini tek, sıralı ve çakışmasız bir listeye indirger."""
from __future__ import annotations

from legalai.packages.pii.patterns import Match

# Aynı aralığı birden fazla dedektör yakalarsa, bu öncelik sırasına göre biri seçilir
_PRIORITY = {"IBAN": 0, "TCKN": 1, "TELEFON": 2, "EPOSTA": 3, "PLAKA": 4}


def merge_matches(matches: list[Match]) -> list[Match]:
    ordered = sorted(matches, key=lambda m: (m.start, _PRIORITY.get(m.label, 99), -(m.end - m.start)))
    merged: list[Match] = []
    last_end = -1
    for m in ordered:
        if m.start >= last_end:
            merged.append(m)
            last_end = m.end
    return merged
