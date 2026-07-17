"""Mandatory local PII boundary for LegalAI-initiated external calls."""
from __future__ import annotations

from legalai.packages.pii.gateway import PiiGateway


async def mask_for_external(text: str, gateway: PiiGateway | None = None) -> str:
    """Mask detected PII before LegalAI sends text to an external service."""
    return await (gateway or PiiGateway()).mask(text)
