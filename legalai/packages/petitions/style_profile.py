"""Local-derived pleading style signals without raw examples or training data."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Iterable


@dataclass(frozen=True)
class StyleProfile:
    profile_id: str
    heading_signals: tuple[str, ...]
    citation_signals: tuple[str, ...]
    tone: str
    argument_order: tuple[str, ...]
    average_paragraph_words: int
    example_count: int
    pii_detected: bool

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["heading_signals"] = list(self.heading_signals)
        payload["citation_signals"] = list(self.citation_signals)
        payload["argument_order"] = list(self.argument_order)
        payload["privacy"] = {
            "raw_examples_persisted": False,
            "pii_detected": self.pii_detected,
            "training_boundary": "local-derived style metadata only; examples are not GPT/Claude/Codex training data",
            "clear_behavior": "Clear the local profile metadata to remove the derived style profile.",
        }
        return payload


def build_style_profile(example_texts: Iterable[str], profile_id: str = "local-default") -> StyleProfile:
    examples = tuple(text for text in example_texts if str(text).strip())
    if not examples:
        raise ValueError("At least one non-empty example is required.")
    joined = "\n".join(examples)
    redacted, pii_types = _redact_pii(joined)
    headings = _heading_signals(redacted)
    citations = _citation_signals(redacted)
    order = _argument_order(redacted)
    paragraphs = [part.split() for part in re.split(r"\n+", redacted) if part.strip()]
    average = round(sum(len(item) for item in paragraphs) / len(paragraphs)) if paragraphs else 0
    tone = "formal" if any(term in redacted.casefold() for term in ("saygılarımla", "arz ederim", "saygilarimla", "arz ederim")) else "neutral-formal"
    return StyleProfile(
        profile_id=profile_id,
        heading_signals=tuple(headings),
        citation_signals=tuple(citations),
        tone=tone,
        argument_order=tuple(order),
        average_paragraph_words=average,
        example_count=len(examples),
        pii_detected=bool(pii_types),
    )


def _redact_pii(text: str) -> tuple[str, set[str]]:
    found: set[str] = set()
    patterns = {
        "email": r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b",
        "iban": r"\bTR\d{2}(?:\s?\d{4}){5}\b",
        "turkish_id": r"\b\d{11}\b",
        "phone": r"\b(?:\+90|0)?\s?5\d{2}\s?\d{3}\s?\d{2}\s?\d{2}\b",
    }
    redacted = text
    for kind, pattern in patterns.items():
        redacted, count = re.subn(pattern, f"[{kind.upper()}]", redacted, flags=re.I)
        if count:
            found.add(kind)
    return redacted, found


def _heading_signals(text: str) -> list[str]:
    signals: list[str] = []
    for line in text.splitlines():
        clean = line.strip()
        if not clean or len(clean) > 100:
            continue
        if clean.isupper() or re.match(r"^\d+(?:\.\d+)*\s+", clean):
            normalized = re.sub(r"^\d+(?:\.\d+)*\s*", "", clean).strip()
            if normalized and normalized not in signals:
                signals.append(normalized)
    return signals[:20]


def _citation_signals(text: str) -> list[str]:
    patterns = (
        r"Yargıtay\s+[^,.;\n]+",
        r"Danıştay\s+[^,.;\n]+",
        r"E\.\s*\d{4}/\d+",
        r"K\.\s*\d{4}/\d+",
        r"m\.\s*\d+",
    )
    return list(dict.fromkeys(pattern for pattern in patterns if re.search(pattern, text, flags=re.I)))


def _argument_order(text: str) -> list[str]:
    candidates = (("olaylar", ("olay", "maddi vakıa", "maddi vakia")), ("hukuki_nedenler", ("hukuki neden", "hukuki değerlendirme")), ("deliller", ("delil", "kanıt", "kanit")), ("talep_sonucu", ("sonuç ve istem", "sonuc ve istem")))
    positions = []
    lowered = text.casefold()
    for label, terms in candidates:
        hits = [lowered.find(term) for term in terms if lowered.find(term) >= 0]
        if hits:
            positions.append((min(hits), label))
    return [label for _, label in sorted(positions)]
