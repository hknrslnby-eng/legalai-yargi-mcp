"""SocratLegal's local corpus and federated retrieval domain."""

from .federated import FederatedRetriever, SourceSearchResult
from .models import CorpusDocument, SourceRecord
from .store import CorpusStore

__all__ = ["CorpusDocument", "CorpusStore", "FederatedRetriever", "SourceRecord", "SourceSearchResult"]
