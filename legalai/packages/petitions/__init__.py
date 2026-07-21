"""Source-grounded general petition operations."""

from .models import PetitionOperation, PetitionRequest, PetitionResult
from .service import process_petition

__all__ = ["PetitionOperation", "PetitionRequest", "PetitionResult", "process_petition"]
