"""Çoklu hukuk alanı ve alt uzmanlık seçimi."""
from __future__ import annotations

from dataclasses import dataclass, field

from legalai.packages.jurisdictions.keywords import JURISDICTION_KEYWORDS


_LENS_KEYWORDS: dict[str, tuple[str, ...]] = {
    "sozlesmeler": ("sözleşme", "fesih", "cezai şart"),
    "kira": ("kira", "kiracı", "kiraya veren"),
    "tazminat": ("tazminat", "haksız fiil", "zararın giderimi"),
    "haksiz_rekabet": ("haksız rekabet", "ticari itibar", "iltibas"),
    "marka": ("marka", "marka hakkı"),
    "patent": ("patent", "buluş"),
    "ticaret": ("ticaret", "şirket", "ticari iş"),
}


@dataclass
class JurisdictionSelection:
    primary: str
    supporting: list[str] = field(default_factory=list)
    expert_lenses: list[str] = field(default_factory=list)
    confidence: float = 0.0
    assumptions: list[str] = field(default_factory=list)
    scores: dict[str, int] = field(default_factory=dict)


def _score_question(question: str) -> dict[str, int]:
    lowered = question.lower()
    return {
        jid: hits
        for jid, keywords in JURISDICTION_KEYWORDS.items()
        if (hits := sum(1 for keyword in keywords if keyword.lower() in lowered))
    }


def _detect_lenses(question: str) -> list[str]:
    lowered = question.lower()
    return [
        lens
        for lens, keywords in _LENS_KEYWORDS.items()
        if any(keyword.lower() in lowered for keyword in keywords)
    ]


def guess_jurisdictions(question: str) -> JurisdictionSelection:
    scores = _score_question(question)
    lenses = _detect_lenses(question)
    if not scores:
        return JurisdictionSelection(
            primary="diger",
            expert_lenses=lenses,
            assumptions=["Soruda belirli bir hukuk alanı güvenle tespit edilemedi."],
        )

    primary = max(scores, key=lambda jid: scores[jid])
    top_score = scores[primary]
    supporting = [
        jid for jid, score in scores.items()
        if jid != primary and score >= max(1, top_score - 1)
    ]
    confidence = top_score / sum(scores.values())
    return JurisdictionSelection(
        primary=primary,
        supporting=supporting,
        expert_lenses=lenses,
        confidence=round(confidence, 3),
        scores=scores,
    )
