import json
import logging
import os

from google.genai import types
from groq import Groq
from pydantic import BaseModel, ValidationError

from app.agent.schemas import (
    AgentResponse,
    AnswerDraft,
    ConfidenceAssessment,
    RetrievalPlan,
)
from app.agent.sql_tool import (
    execute_structured_query,
    search_structured_records,
)
from app.rag.embeddings import client
from app.rag.retriever import retrieve_relevant_chunks


logger = logging.getLogger(__name__)

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

groq_client = (
    Groq(api_key=os.getenv("GROQ_API_KEY"))
    if os.getenv("GROQ_API_KEY")
    else None
)


PLANNER_PROMPT = """
You are the retrieval planner for Veloxa CXO Cockpit.

Understand the user's question and decide which data sources are required.

Available retrieval sources:

1. sql: Structured records stored in PostgreSQL, originating from CSV and Excel.
2. rag: Unstructured documents stored as document chunks with embeddings.

Choose SQL for:
- Exact figures, counts, totals, averages and comparisons.
- Employee records, payroll and hiring.
- Jira issues, incidents and leave records.
- Other structured facts.

Choose RAG for:
- Explanations, policies and emails.
- Meeting notes and board updates.
- Invoices and document context.
- Narrative information.

Choose both when structured facts and supporting document context are needed.

For SQL questions, prefer structured_query over generic search_terms.

Available structured sources and sheets:

1. Employee_Master.xlsx
   Sheet: Employees

2. Hiring_Tracker.xlsx
   Sheet: Requisitions

3. Jira_Export_ATLAS.xlsx
   Sheets: Issues, Epics, Versions

4. Incidents_Aug-Oct_2026.xlsx
   Sheet: Incidents

5. Payroll_Register_Jan-Mar_2026.xlsx
   Sheet: Payroll Q4

6. Leave_Register.xlsx
   Sheet: Leave

7. OnCall_Rota.xlsx
   Sheet: OnCall Rota

8. Pulse_Survey.xlsx
   Sheet: Pulse Survey

9. GL_Export_Apr-Sep_2026.xlsx
   Sheet: GL

10. Evidence_Index.xlsx
    Sheet: Evidence Index

Structured query operations:

- search: retrieve matching records.
- count: count matching records.
- group_count: count records grouped by a field.
- sum: calculate the sum of a numeric field.
- group_sum: calculate sums grouped by a field.

Structured query rules:

- Use exact source_file and sheet names.
- Use only fields that exist in the selected sheet.
- Use filters to narrow the records.
- Supported filter operators are equals, contains and in.
- Use in when filtering for multiple values.
- For group_count, provide group_by.
- For sum, provide field.
- For group_sum, provide both field and group_by.
- Use a limit not exceeding 25.
- Do not invent source files, sheets, fields or values.
- If SQL is not needed, set structured_query to null.
- If SQL is needed but a structured query cannot be constructed reliably,
  use search_terms as a fallback.

Return only valid JSON matching the RetrievalPlan schema.
"""


ANSWER_PROMPT = """
You are the main answering agent for Veloxa CXO Cockpit.

Answer the user's question using only the supplied evidence.

Rules:

1. Do not invent facts, numbers, names, dates or explanations.
2. Use SQL evidence for exact structured figures and calculations.
3. Use RAG evidence for document-based information and context.
4. If evidence from multiple sources is available, combine it carefully.
5. If sources conflict, explicitly mention the conflict.
6. If evidence is insufficient, clearly state what cannot be determined.
7. Cite evidence using its evidence_id, such as [SQL-1] or [RAG-1].
8. Do not claim that a query returned a complete result if it was truncated.
9. Keep the answer clear, direct and relevant to the question.

Return only valid JSON matching the AnswerDraft schema.
"""


class GeminiServiceError(Exception):
    """Raised when the configured AI providers cannot generate a response."""


def _is_retryable_provider_error(error: Exception) -> bool:
    """Determine whether a Gemini failure should trigger Groq fallback."""

    status_code = getattr(error, "status_code", None)

    if status_code in {408, 409, 429, 500, 502, 503, 504}:
        return True

    error_name = type(error).__name__.lower()

    retryable_names = (
        "servererror",
        "toomanyrequests",
        "resourceexhausted",
        "deadlineexceeded",
        "serviceunavailable",
        "timeouterror",
        "connectionerror",
    )

    if any(name in error_name for name in retryable_names):
        return True

    message = str(error).lower()

    retryable_messages = (
        "high demand",
        "temporarily unavailable",
        "rate limit",
        "resource exhausted",
        "timeout",
        "timed out",
        "connection error",
        "service unavailable",
        "503",
        "429",
    )

    return any(item in message for item in retryable_messages)


def _generate_with_groq(
    prompt: str,
    response_model: type[BaseModel],
) -> BaseModel:
    """Generate and validate a JSON response using Groq."""

    if groq_client is None:
        raise GeminiServiceError(
            "Groq fallback is unavailable because GROQ_API_KEY is not configured."
        )

    try:
        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )

        content = response.choices[0].message.content

        if not content:
            raise ValueError("Groq returned an empty response.")

        parsed_json = json.loads(content)

        return response_model.model_validate(parsed_json)

    except (ValidationError, json.JSONDecodeError, ValueError):
        logger.exception("Groq returned an invalid response.")
        raise

    except Exception as error:
        logger.exception("Groq generation failed.")

        raise GeminiServiceError(
            "The primary and fallback AI providers could not complete the request."
        ) from error


def _generate_json(
    prompt: str,
    response_model: type[BaseModel],
) -> BaseModel:
    """
    Use Gemini as the primary provider.
    Use Groq when Gemini encounters a retryable provider failure.
    """

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=response_model,
                temperature=0.1,
            ),
        )

        if not response.text:
            raise ValueError("Gemini returned an empty response.")

        parsed_json = json.loads(response.text)

        return response_model.model_validate(parsed_json)

    except (ValidationError, json.JSONDecodeError, ValueError):
        logger.exception("Gemini returned an invalid response.")
        raise

    except Exception as error:
        if not _is_retryable_provider_error(error):
            logger.exception(
                "Gemini generation failed with a non-retryable error."
            )

            raise GeminiServiceError(
                "Gemini could not complete the request."
            ) from error

        logger.warning(
            "Gemini encountered a retryable failure. "
            "Attempting Groq fallback."
        )

        return _generate_with_groq(prompt, response_model)


def _plan(question: str) -> RetrievalPlan:
    """Create a retrieval plan for the user's question."""

    prompt = (
        f"{PLANNER_PROMPT}\n\n"
        f"User question:\n{question}"
    )

    plan = _generate_json(prompt, RetrievalPlan)

    plan.sources = list(dict.fromkeys(plan.sources))

    plan.search_terms = [
        term.strip()
        for term in plan.search_terms
        if term and term.strip()
    ][:6]

    return plan


def _sql_evidence(rows: list[dict]) -> list[dict]:
    """Convert generic SQL search results into evidence objects."""

    evidence = []

    for index, row in enumerate(rows, start=1):
        evidence.append(
            {
                "evidence_id": f"SQL-{index}",
                "source": "sql",
                "source_reference": {
                    "file_name": row.get("file_name"),
                    "sheet_name": row.get("sheet_name"),
                    "record_id": row.get("record_id"),
                },
                "content": row,
            }
        )

    return evidence


def _structured_sql_evidence(
    result: dict,
    plan,
) -> list[dict]:
    """Convert a structured SQL query result into evidence."""

    return [
        {
            "evidence_id": "SQL-1",
            "source": "sql",
            "source_reference": {
                "file_name": plan.source_file,
                "sheet": plan.sheet,
                "operation": plan.operation,
                "field": plan.field,
                "group_by": plan.group_by,
                "filters": [
                    item.model_dump()
                    for item in plan.filters
                ],
            },
            "content": result,
        }
    ]


def _rag_evidence(
    chunks: list[dict],
    start_index: int = 1,
) -> list[dict]:
    """Convert retrieved document chunks into evidence objects."""

    evidence = []

    for index, chunk in enumerate(chunks, start=start_index):
        evidence.append(
            {
                "evidence_id": f"RAG-{index}",
                "source": "rag",
                "source_reference": {
                    "file_name": (
                        chunk.get("file_name")
                        or chunk.get("source_file")
                    ),
                    "source_path": chunk.get("source_path"),
                    "chunk_index": chunk.get("chunk_index"),
                },
                "content": (
                    chunk.get("content")
                    or chunk.get("text")
                    or chunk.get("chunk_text")
                    or ""
                ),
                "similarity": chunk.get("similarity"),
            }
        )

    return evidence


def _confidence(
    sql_count: int,
    rag_count: int,
    conflicts: list[str],
) -> ConfidenceAssessment:
    """Estimate confidence based on retrieved evidence."""

    if conflicts:
        return ConfidenceAssessment(
            level="low",
            rationale=(
                "The retrieved evidence contains conflicting information."
            ),
        )

    if sql_count > 0 and rag_count > 0:
        return ConfidenceAssessment(
            level="high",
            rationale=(
                "The answer is supported by both structured SQL records "
                "and relevant document evidence."
            ),
        )

    if sql_count > 0 or rag_count > 0:
        return ConfidenceAssessment(
            level="moderate",
            rationale=(
                "The answer is supported by retrieved evidence from "
                "at least one available source."
            ),
        )

    return ConfidenceAssessment(
        level="low",
        rationale="No supporting evidence was retrieved.",
    )


def answer_question(question: str) -> AgentResponse:
    """
    Main agent workflow:

    1. Understand the question.
    2. Decide whether SQL, RAG or both are required.
    3. Retrieve the required evidence.
    4. Generate the final answer using Gemini or Groq fallback.
    5. Return the answer with evidence and confidence.
    """

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    plan = _plan(question)

    evidence = []
    limitations = []

    sql_count = 0
    rag_count = 0

    # ---------------------------------------------------------
    # Structured SQL retrieval
    # ---------------------------------------------------------

    if "sql" in plan.sources:
        try:
            if plan.structured_query is not None:
                query_plan = plan.structured_query.model_dump()

                result = execute_structured_query(query_plan)

                sql_items = _structured_sql_evidence(
                    result,
                    plan.structured_query,
                )

                if result.get("truncated"):
                    limitations.append(
                        "Structured SQL query results were truncated."
                    )

                if not result.get("results"):
                    limitations.append(
                        "The structured SQL query did not return matching records."
                    )

            else:
                rows = search_structured_records(plan.search_terms)

                sql_items = _sql_evidence(rows)

                if not rows:
                    limitations.append(
                        "No matching structured records were found."
                    )

            evidence.extend(sql_items)
            sql_count = len(sql_items)

        except Exception:
            logger.exception("Structured record retrieval failed.")

            limitations.append(
                "Structured record retrieval was unavailable."
            )

    # ---------------------------------------------------------
    # RAG retrieval
    # ---------------------------------------------------------

    if "rag" in plan.sources:
        try:
            rag_query = plan.rag_query.strip() or question

            chunks = retrieve_relevant_chunks(
                rag_query,
                top_k=5,
            )

            rag_items = _rag_evidence(chunks)

            evidence.extend(rag_items)
            rag_count = len(rag_items)

            if not chunks:
                limitations.append(
                    "No relevant document chunks were found."
                )

        except Exception:
            logger.exception("Document retrieval failed.")

            limitations.append(
                "Document retrieval was unavailable."
            )

    # ---------------------------------------------------------
    # No evidence found
    # ---------------------------------------------------------

    if not evidence:
        empty_result_messages = {
            "No matching structured records were found.",
            "No relevant document chunks were found.",
        }

        # When both sources return no results, report one clear limitation.
        if (
            not limitations
            or all(
                item in empty_result_messages
                for item in limitations
            )
        ):
            limitations = [
                "No supporting evidence was found."
            ]

        return AgentResponse(
            question=question,
            answer=(
                "I cannot determine the answer from the available "
                "structured records and documents."
            ),
            retrieval_sources=[],
            evidence=[],
            confidence=ConfidenceAssessment(
                level="low",
                rationale=(
                    "No usable supporting evidence was retrieved "
                    "from the available data sources."
                ),
            ),
            limitations=limitations,
        )

    # ---------------------------------------------------------
    # Final answer generation
    # ---------------------------------------------------------

    answer_prompt = (
        f"{ANSWER_PROMPT}\n\n"
        f"User question:\n{question}\n\n"
        f"Retrieved evidence:\n"
        f"{json.dumps(evidence, indent=2, default=str)}\n\n"
        f"Known limitations:\n"
        f"{json.dumps(limitations, indent=2)}"
    )

    try:
        answer_draft = _generate_json(
            answer_prompt,
            AnswerDraft,
        )

    except Exception as error:
        logger.exception("Final answer generation failed.")

        raise GeminiServiceError(
            "The AI agent could not generate the final answer."
        ) from error

    # ---------------------------------------------------------
    # Conflict reporting
    # ---------------------------------------------------------

    if answer_draft.conflicts:
        limitations.extend(
            f"Conflicting evidence: {conflict}"
            for conflict in answer_draft.conflicts
        )

    # ---------------------------------------------------------
    # Confidence and final response
    # ---------------------------------------------------------

    confidence = _confidence(
        sql_count=sql_count,
        rag_count=rag_count,
        conflicts=answer_draft.conflicts,
    )

    all_limitations = list(
        dict.fromkeys(
            limitations + answer_draft.limitations
        )
    )

    retrieval_sources = []

    if sql_count > 0:
        retrieval_sources.append("sql")

    if rag_count > 0:
        retrieval_sources.append("rag")

    return AgentResponse(
        question=question,
        answer=answer_draft.answer,
        retrieval_sources=retrieval_sources,
        evidence=evidence,
        confidence=confidence,
        limitations=all_limitations,
    )
