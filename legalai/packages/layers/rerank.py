"""Rerank — RetrieveDocuments'ın getirdiği belgeleri sorudaki kelimelerle
örtüşme skoruna göre yeniden sıralar ve en iyi `top_k` belgeye indirir.

Bkz. FORK-KAPSAMLI-PLAN.md §5.1 ("Rerank top-5") ve Hafta 7 agent
promptu ("retrieve + rerank + tüm katmanlar"). Gerçek bir cross-encoder
yeniden sıralayıcı yerine basit bir sözcük-örtüşme skoru kullanılır;
embedding tabanlı reranker, pgvector/qdrant entegrasyonuyla birlikte
(§8.2) eklenecek — arayüz (bu katmanın `run` imzası) değişmeyecek.
"""
from __future__ import annotations

import re

from legalai.packages.layers.pipeline import Context
from legalai.packages.shared.types import Document

_WORD_RE = re.compile(r"[a-zA-ZçğıöşüÇĞİÖŞÜ]+")


def _tokenize(text: str) -> set[str]:
    return {w.lower() for w in _WORD_RE.findall(text) if len(w) > 2}


def score_document(query_tokens: set[str], doc_body: str) -> float:
    """Sorudaki benzersiz kelimelerin ne kadarının belgede geçtiğini (0-1
    arası) döner. Sorgu boşsa veya belge boşsa 0.0."""
    if not query_tokens:
        return 0.0
    doc_tokens = _tokenize(doc_body)
    if not doc_tokens:
        return 0.0
    overlap = query_tokens & doc_tokens
    return len(overlap) / len(query_tokens)


class Rerank:
    name = "rerank"

    def __init__(self, top_k: int = 5) -> None:
        self._top_k = top_k

    async def run(self, ctx: Context) -> Context:
        query_tokens = _tokenize(ctx.question)
        scored: list[tuple[float, Document]] = [
            (score_document(query_tokens, doc.body), doc) for doc in ctx.documents
        ]
        scored.sort(key=lambda pair: pair[0], reverse=True)

        ctx.scored = [{"doc_id": doc.id, "score": round(score, 4)} for score, doc in scored]
        ctx.documents = [doc for _, doc in scored[: self._top_k]]
        return ctx
