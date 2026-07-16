"""İç HTTP endpoint'leri — ileride Next.js web UI için. Bkz.
FORK-KAPSAMLI-PLAN.md §2.6 ve §5, Hafta 7. Aynı iş mantığını
(`run_pipeline`) MCP tool'u da çağırır — bkz. `legalai/apps/mcp/server.py`.
"""
from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from legalai.packages.layers.analysis_pipeline import run_pipeline
from legalai.packages.layers.opposing import run_opposing

router = APIRouter(prefix="/api/v1", tags=["legalai"])


class AnalyzeRequest(BaseModel):
    question: str = Field(..., min_length=1)
    mode: str = "layered"
    jurisdiction_hint: str | None = None


class SourceModel(BaseModel):
    doc_id: str
    citation: str
    source: str


class AnalyzeResponse(BaseModel):
    question: str
    mode: str
    jurisdiction_id: str | None
    answer: str | None
    citations: list[str]
    sources: list[SourceModel]
    trace: list[dict]
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    temporal_context: dict[str, Any] | None = None
    deadline_risks: list[dict[str, Any]] = Field(default_factory=list)
    forum_candidates: list[dict[str, Any]] = Field(default_factory=list)
    strategy_options: list[dict[str, Any]] = Field(default_factory=list)
    analysis_only: bool = True
    non_binding: bool = True
    confidence: float = 0.0
    assumptions: list[str] = Field(default_factory=list)
    missing_facts: list[str] = Field(default_factory=list)
    source_scope: str = "targeted"

    @classmethod
    def from_domain(cls, result) -> "AnalyzeResponse":
        data = result.to_dict()
        return cls(
            question=data["question"],
            mode=data["mode"],
            jurisdiction_id=data["jurisdiction_id"],
            answer=data["answer"],
            citations=data["citations"],
            sources=[SourceModel(**s) for s in data["sources"]],
            trace=data["trace"],
            evidence=data.get("evidence", []),
            temporal_context=data.get("temporal_context"),
            deadline_risks=data.get("deadline_risks", []),
            forum_candidates=data.get("forum_candidates", []),
            strategy_options=data.get("strategy_options", []),
            analysis_only=True,
            non_binding=True,
            confidence=data.get("confidence", 0.0),
            assumptions=data.get("assumptions", []),
            missing_facts=data.get("missing_facts", []),
            source_scope=data.get("source_scope", "targeted"),
        )


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    result = await run_pipeline(
        question=req.question,
        mode=req.mode,
        jurisdiction_hint=req.jurisdiction_hint,
    )
    return AnalyzeResponse.from_domain(result)


class OpposingRequest(BaseModel):
    question: str = Field(..., min_length=1)
    position: str = Field(..., min_length=1)
    role: Literal["davacı", "davalı", "sanık", "katılan", "başvurucu", "karşı_taraf", "idare"] = "davacı"
    jurisdiction_hint: str | None = None
    source_scope: Literal["targeted", "all", "selected"] = "targeted"
    selected_source_ids: list[str] = Field(default_factory=list)
    synthesize: bool = False


class OpposingResponse(BaseModel):
    model_config = ConfigDict(extra="allow")


@router.post("/opposing")
async def opposing(req: OpposingRequest) -> dict[str, Any]:
    result = await run_opposing(
        question=req.question,
        position=req.position,
        role=req.role,
        jurisdiction_hint=req.jurisdiction_hint,
        source_scope=req.source_scope,
        selected_source_ids=req.selected_source_ids,
        synthesize=req.synthesize,
    )
    return result.to_dict()


class HealthResponse(BaseModel):
    status: str = "ok"


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse()
