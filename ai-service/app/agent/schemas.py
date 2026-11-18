from typing import Literal

from pydantic import BaseModel, Field


class AgentAskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class RetrievalPlan(BaseModel):
    sources: list[Literal["sql", "rag"]] = Field(max_length=2)
    search_terms: list[str] = Field(default_factory=list, max_length=6)
    rag_query: str = Field(default="", max_length=500)


class AnswerDraft(BaseModel):
    answer: str
    conflicts: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class ConfidenceAssessment(BaseModel):
    level: Literal["low", "moderate", "high"]
    rationale: str


class AgentResponse(BaseModel):
    question: str
    answer: str
    retrieval_sources: list[str]
    evidence: list[dict]
    confidence: ConfidenceAssessment
    limitations: list[str]
