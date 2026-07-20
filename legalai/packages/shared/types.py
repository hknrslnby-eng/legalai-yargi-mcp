"""Katmanlar arasında paylaşılan ortak veri tipleri (yargı türünden bağımsız)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Document:
    """Pipeline'ın işlediği ham belge (karar metni)."""

    id: str
    body: str
    source: str = ""       # yargitay | danistay | aihm | kik | ...
    citation: str = ""
    source_url: str = ""
    metadata: dict[str, Any] | None = None
