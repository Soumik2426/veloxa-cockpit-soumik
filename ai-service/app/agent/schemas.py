from typing import Any, Literal

from pydantic import BaseModel, Field


class AgentAskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class StructuredQueryFilter(BaseModel):
    field: str = Field(min_length=1, max_length=100)
    operator: Literal["equals", "contains", "in"]
    value: str | int | float | list[str]


class StructuredQueryPlan(BaseModel):
    source_file: str = Field(min_length=1, max_length=200)
    sheet: str = Field(min_length=1, max_length=100)

    operation: Literal[
        "search",
        "count",
        "group_count",
        "sum",
        "group_sum",
    ]

    field: str | None = Field(default=None, max_length=100)
    group_by: str | None = Field(default=None, max_length=100)

    filters: list[StructuredQueryFilter] = Field(
        default_factory=list,
        max_length=10,
    )

    limit: int = Field(default=25, ge=1, le=25)


class RetrievalPlan(BaseModel):
    sources: list[Literal["sql", "rag"]] = Field(max_length=2)
    search_terms: list[str] = Field(default_factory=list, max_length=6)
    rag_query: str = Field(default="", max_length=500)

    # Optional for backward compatibility with generic SQL searches.
    structured_query: StructuredQueryPlan | None = None


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
    evidence: list[dict[str, Any]]
    confidence: ConfidenceAssessment
    limitations: list[str]
