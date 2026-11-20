from typing import Any, Literal
from datetime import date
from pydantic import BaseModel, Field, model_validator


class AgentAskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class StructuredQueryFilter(BaseModel):
    field: str = Field(min_length=1, max_length=100)
    operator: Literal["equals", "contains", "in", "between"]
    value: str | int | float | list[str] | list[int] | list[float]

    @model_validator(mode="after")
    def validate_filter_value(self):
        if self.operator == "between":
            if not isinstance(self.value, list) or len(self.value) != 2:
                raise ValueError("The 'between' operator requires exactly two values.")
            if not all(isinstance(item, (str, int, float)) for item in self.value):
                raise ValueError("The 'between' values must be text or numbers.")
        elif self.operator == "in":
            if not isinstance(self.value, list) or not self.value:
                raise ValueError("The 'in' operator requires a non-empty list.")
        elif isinstance(self.value, list):
            raise ValueError("Only 'in' and 'between' accept list values.")
        return self


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

    @model_validator(mode="after")
    def validate_operation_fields(self):
        if self.operation in {"sum", "group_sum"} and not self.field:
            raise ValueError("A field is required for sum operations.")

        if self.operation in {"group_count", "group_sum"} and not self.group_by:
            raise ValueError("A group_by field is required for grouped operations.")

        if self.operation == "group_sum" and self.field == self.group_by:
            raise ValueError("The aggregation and grouping fields must differ.")

        return self


class RetrievalPlan(BaseModel):
    sources: list[Literal["sql", "rag"]] = Field(max_length=2)

    search_terms: list[str] = Field(
        default_factory=list,
        max_length=6,
    )

    rag_query: str = Field(
        default="",
        max_length=500,
    )

    # Backward compatibility with existing single-query plans.
    structured_query: StructuredQueryPlan | None = None

    # Supports multi-sheet and dependent lookups.
    structured_queries: list[StructuredQueryPlan] = Field(
        default_factory=list,
        max_length=10,
    )


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


class EmployeeMemoryContext(BaseModel):
    memory_type: Literal["FACT", "PREFERENCE", "COMMITMENT", "ASSUMPTION"]
    content: str = Field(min_length=1, max_length=4000)
    source_references: dict[str, Any] = Field(default_factory=dict)
    confidence: float | None = Field(default=None, ge=0, le=1)


class EmployeeAgentContext(BaseModel):
    employee_code: str = Field(min_length=1, max_length=20)
    full_name: str = Field(min_length=1, max_length=150)
    title: str = Field(min_length=1, max_length=150)
    department: str | None = Field(default=None, max_length=100)
    manager: dict[str, Any] | None = None
    responsibilities: list[str] = Field(default_factory=list, max_length=20)
    professional_background: str | None = Field(default=None, max_length=2000)
    relevant_colleagues: list[dict[str, Any]] = Field(
        default_factory=list,
        max_length=50,
    )
    department_context: dict[str, Any] = Field(default_factory=dict)
    conversation_history: list[dict[str, Any]] = Field(
        default_factory=list,
        max_length=20,
    )
    persona_config: dict[str, Any] = Field(default_factory=dict)
    system_context: str | None = Field(default=None, max_length=8000)
    memories: list[EmployeeMemoryContext] = Field(default_factory=list, max_length=50)
    as_of_date: date | None = None


class EmployeeAgentRespondRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    employee_context: EmployeeAgentContext

