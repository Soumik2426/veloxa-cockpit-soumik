import json
import logging
import os
import re

from google.genai import types
from groq import Groq
from pydantic import BaseModel, ValidationError

from app.agent.schemas import (
    AgentResponse,
    AnswerDraft,
    ConfidenceAssessment,
    RetrievalPlan,
    StructuredQueryPlan,
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

Understand the user's question and construct accurate retrieval plans.

AVAILABLE SOURCES

1. sql: Structured PostgreSQL records originating from CSV and Excel.
2. rag: Unstructured documents, transcripts, emails and PDFs.

Choose SQL for:
- Exact figures, counts, totals, averages and comparisons.
- Employees, managers, payroll and hiring.
- Jira issues, epics, story points and incidents.
- Structured dates, statuses and relationships.

Choose RAG for:
- Explanations, policies, emails and meeting notes.
- Board commentary and narrative context.
- Information available only in documents.

Choose both when structured information and document context are required.

AVAILABLE STRUCTURED SCHEMAS

Employee_Master.xlsx / Employees:
Department, Emp ID, Exit Date, Full Name, Join Date,
Location, Manager ID, Status, Title, Work Email.

Hiring_Tracker.xlsx / Requisitions:
Role, Team, Notes, Opened, Req ID, Status,
Status Date, In pipeline, Hiring Manager.

Jira_Export_ATLAS.xlsx / Issues:
Assignee, Created, Epic Link, Key, Last Changed,
Resolved, Status, Story Points, Summary, Type.

Jira_Export_ATLAS.xlsx / Epics:
Key, Epic Name.

Jira_Export_ATLAS.xlsx / Versions:
Version, Changed By, Last Changed,
Release Date, Original Release Date.

Incidents_Aug-Oct_2026.xlsx / Incidents:
ID, Opened, Resolved, Responder, Service, Severity.

Payroll_Register_Jan-Mar_2026.xlsx / Payroll Q4:
Days in Month, Days Payable, Deductions (Rs.),
Emp ID, Gross (Rs.), Month, Name, Net (Rs.), Processed By.

Leave_Register.xlsx / Leave.

OnCall_Rota.xlsx / OnCall Rota.

Pulse_Survey.xlsx / Pulse Survey:
Comments, Engagement (1-5), Quarter,
Responses, Team, Team size.

GL_Export_Apr-Sep_2026.xlsx / GL:
Amount (Rs.), Cost Centre, Entered By,
Narration, Ref, Txn Date, Vendor / Payee, Voucher.

Evidence_Index.xlsx / Evidence Index:
Confidence (H/M/L), Date (as written),
Date (normalised, IST), Entities named,
Fact (your words), File, Ref, Sheet / page / row.

AVAILABLE SQL OPERATIONS

- search
- count
- group_count
- sum
- group_sum

FILTER OPERATORS

- equals
- contains
- in

IMPORTANT QUERY CONSTRUCTION RULES

1. Always use exact source_file and sheet names.
2. Use only fields present in the selected sheet.
3. Use structured_query or structured_queries for structured questions.
4. Do not use generic search_terms when a structured query can answer the question.
5. Use structured_queries when information is needed from multiple sheets.
6. You may provide up to 10 structured queries.
7. Do not duplicate the same query.
8. Do not invent values, fields, sources or records.
9. Use limit <= 25 for search.
10. Use group_count for grouped counts.
11. Use group_sum for grouped numeric totals.
12. Use in when filtering for multiple values.

EMPLOYEE REFERENCE RESOLUTION

Employee IDs and Manager IDs are references to employee records.

When asked who an employee reports to:
- Query Employees using the employee's Full Name or Emp ID.
- Retrieve their Manager ID.
- Do NOT invent or guess the Manager ID in a second query. The application will
  execute the dependent manager lookup after retrieving the first employee record.
- Retrieve the manager's Full Name, Title, Department and Location when evidence is available.

When asked about a manager's additional information:
- Query Employees using Emp ID equal to the requested Manager ID.
- Query Employees using Manager ID equal to that same ID.
- The first query retrieves the manager's own record.
- The second retrieves the manager's direct reports.

Never present an employee ID as a person's name when the name can be retrieved.

HIRING RULES

For requisition questions:
- Query Hiring_Tracker.xlsx / Requisitions.
- Use Req ID for exact requisition lookups.
- Retrieve Role, Status, Status Date, In pipeline, Hiring Manager and Notes.
- For questions about requisitions on hold, filter Status = On hold.
- For currently open requisitions, filter Status = Open.
- Do not confuse the number of candidates in the pipeline with the number of requisitions.

JIRA RULES

For issue status counts:
- Use group_count grouped by Status.

For completed story points:
- Use sum of Story Points with Status = Done.

For open story points:
- Use sum of Story Points with Status in ["In Progress", "To Do"].

For open story points by assignee:
- Use group_sum on Story Points grouped by Assignee.
- Filter Status in ["In Progress", "To Do"].

For an epic's open story points:
- Query Epics using Key to retrieve the epic name.
- Query Issues using Epic Link equal to the requested epic key.
- Exclude Status = Done by filtering Status in ["In Progress", "To Do"].
- Use group_sum or sum on Story Points as appropriate.
- Do not claim an epic's own status from the Epics sheet because that sheet does not contain a Status field.

For release-date history:
- Query Versions.
- Retrieve Original Release Date, Release Date, Changed By and Last Changed.

PAYROLL RULES

For monthly or quarterly payroll:
- Use Payroll_Register_Jan-Mar_2026.xlsx / Payroll Q4.
- Use group_sum on Gross (Rs.) grouped by Month for monthly totals.
- Filter Month using the exact month values requested.
- For a quarterly total, also retrieve a sum across the requested months.
- Do not confuse gross payroll with net payroll.
- Do not assume that every month has the same employee count.

INCIDENT RULES

For incident counts by service:
- Use group_count grouped by Service.
- For the service with the most incidents, compare all returned groups.

MULTI-SHEET RULES

Use separate structured queries for each required sheet.

For employee relationships, use dependent queries where necessary.

For quarter comparisons, use separate queries for each source or period.

If a question needs a grouped result and an overall total, use separate queries.

Return only valid JSON matching RetrievalPlan.
"""


ANSWER_PROMPT = """
You are the main answering agent for Veloxa CXO Cockpit.

Answer the user's question using only the supplied evidence.

STRICT RULES

1. Never invent facts, figures, names, dates or explanations.
2. Answer every part of a multi-part question.
3. Prefer actual human-readable names over employee IDs.
4. When evidence contains a reference ID, use other retrieved evidence
   to resolve it whenever possible.
5. Do not confuse a manager's own employee record with their direct reports.
6. Use SQL evidence for exact structured figures and calculations.
7. Use RAG evidence for document-based information and context.
8. If multiple sources are available, combine them carefully.
9. If sources conflict, explicitly explain the conflict.
10. If evidence is insufficient, clearly state what cannot be determined.
11. Do not infer a missing field from a related field.
12. Do not claim that a query returned complete results if it was truncated.
13. Do not claim a grouped total is a complete total if some groups are missing.
14. Every factual claim must have supporting evidence citations.
15. Cite exact evidence IDs.
16. Both citation formats are allowed:
    [SQL-1]
    [SQL-1, RAG-1]
17. Never create, modify or guess evidence IDs.
18. Distinguish between actual values and derived calculations.
19. Do not silently omit relevant evidence.
20. If an employee name cannot be resolved, explicitly state that limitation.

Return only valid JSON matching AnswerDraft.
"""


class GeminiServiceError(Exception):
    """Raised when the configured AI providers cannot generate a response."""


def _is_retryable_provider_error(error: Exception) -> bool:
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


def _normalize_groq_response(
    parsed_json: dict,
    response_model: type[BaseModel],
) -> dict:

    if not isinstance(parsed_json, dict):
        raise ValueError("Groq response must be a JSON object.")

    data = dict(parsed_json)

    if response_model is RetrievalPlan:
        if data.get("search_terms") is None:
            data["search_terms"] = []

        if data.get("rag_query") is None:
            data["rag_query"] = ""

        if data.get("structured_query") is None:
            data["structured_query"] = None

        if data.get("structured_queries") is None:
            data["structured_queries"] = []

        if not data.get("sources"):
            inferred_sources = []

            if (
                data.get("structured_query") is not None
                or data.get("structured_queries")
                or data.get("search_terms")
            ):
                inferred_sources.append("sql")

            if (
                isinstance(data.get("rag_query"), str)
                and data["rag_query"].strip()
            ):
                inferred_sources.append("rag")

            if not inferred_sources:
                raise ValueError(
                    "Groq planner response does not identify retrieval sources."
                )

            data["sources"] = list(dict.fromkeys(inferred_sources))

        for query in data.get("structured_queries", []):
            if isinstance(query, dict) and query.get("filters") is None:
                query["filters"] = []

        structured_query = data.get("structured_query")

        if (
            isinstance(structured_query, dict)
            and structured_query.get("filters") is None
        ):
            structured_query["filters"] = []

    return data


def _generate_with_groq(
    prompt: str,
    response_model: type[BaseModel],
) -> BaseModel:

    if groq_client is None:
        raise GeminiServiceError(
            "Groq fallback is unavailable because GROQ_API_KEY is not configured."
        )

    try:
        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1,
        )

        content = response.choices[0].message.content

        if not content:
            raise ValueError("Groq returned an empty response.")

        parsed_json = json.loads(content)

        normalized_json = _normalize_groq_response(
            parsed_json,
            response_model,
        )

        return response_model.model_validate(normalized_json)

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
    Generate JSON using Gemini and validate it locally with Pydantic.

    We intentionally avoid sending the Pydantic model as Gemini's
    response_schema because complex schemas can exceed Gemini's
    supported schema constraints.
    """

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1,
            ),
        )

        if not response.text:
            raise ValueError("Gemini returned an empty response.")

        parsed_json = json.loads(response.text)
        logger.debug(
            "Gemini raw JSON response:\n%s",
            json.dumps(parsed_json, indent=2, ensure_ascii=False)
        )

        if not isinstance(parsed_json, dict):
            raise ValueError("Gemini response must be a JSON object.")

        # Normalize Gemini's planner output to the canonical Pydantic schema.
        if response_model is RetrievalPlan:
            if isinstance(parsed_json.get("retrieval_plan"), dict):
                parsed_json = parsed_json["retrieval_plan"]

            # Some Gemini responses represent sources as objects containing
            # both the source type and the SQL query definitions.
            raw_sources = parsed_json.get("sources", parsed_json.get("target_sources"))
            if raw_sources is None:
                raw_sources = parsed_json.get("source", [])

            normalized_sources = []
            extracted_queries = list(parsed_json.get("structured_queries") or [])

            if isinstance(raw_sources, str):
                raw_sources = [raw_sources]

            if isinstance(raw_sources, list):
                for source_item in raw_sources:
                    if isinstance(source_item, str):
                        normalized_sources.append(source_item)
                        continue

                    if not isinstance(source_item, dict):
                        continue

                    source_type = source_item.get("type") or source_item.get("source")
                    if source_type in {"sql", "rag"}:
                        normalized_sources.append(source_type)

                    # A source object may carry source_file/sheet once, with
                    # one or more queries nested beneath it.
                    nested_queries = source_item.get("structured_queries") or []
                    if isinstance(nested_queries, dict):
                        nested_queries = [nested_queries]

                    for query in nested_queries:
                        if not isinstance(query, dict):
                            continue
                        query = dict(query)
                        query.setdefault("source_file", source_item.get("source_file"))
                        query.setdefault("sheet", source_item.get("sheet"))
                        extracted_queries.append(query)

                    # Also support a source object that is itself one query.
                    if (
                        source_type == "sql"
                        and source_item.get("operation")
                        and not nested_queries
                    ):
                        query = dict(source_item)
                        query.pop("type", None)
                        query.pop("source", None)
                        extracted_queries.append(query)

            parsed_json["sources"] = list(dict.fromkeys(normalized_sources))

            # Map alternate RAG/search field names.
            if "search_terms" not in parsed_json:
                parsed_json["search_terms"] = parsed_json.get("search_queries", [])

            if "rag_query" not in parsed_json:
                rag_queries = parsed_json.get(
                    "rag_queries", parsed_json.get("rag_search_terms", [])
                )
                if isinstance(rag_queries, list):
                    parsed_json["rag_query"] = " ".join(
                        str(item) for item in rag_queries if item
                    )
                else:
                    parsed_json["rag_query"] = str(rag_queries or "")

            # Do not execute incomplete dependent lookups. In particular,
            # Gemini sometimes emits an empty Emp ID while trying to resolve
            # an employee's manager. That ID must come from the first SQL result.
            valid_queries = []
            for query in extracted_queries:
                if not isinstance(query, dict):
                    continue
                filters = query.get("filters") or []
                if any(
                    isinstance(item, dict)
                    and isinstance(item.get("value"), str)
                    and not item["value"].strip()
                    for item in filters
                ):
                    logger.warning(
                        "Skipping structured query containing an empty filter value: %s",
                        query.get("source_file"),
                    )
                    continue
                query.setdefault("filters", [])
                valid_queries.append(query)

            parsed_json["structured_queries"] = valid_queries
            parsed_json.setdefault("structured_query", None)
            parsed_json.setdefault("search_terms", [])
            parsed_json.setdefault("rag_query", "")

            # Infer retrieval sources from the actual work requested if the
            # model omitted or malformed the source list.
            if not parsed_json["sources"]:
                inferred = []
                if valid_queries or parsed_json.get("structured_query") or parsed_json["search_terms"]:
                    inferred.append("sql")
                if parsed_json["rag_query"].strip():
                    inferred.append("rag")
                parsed_json["sources"] = inferred

        elif response_model is AnswerDraft:
            if isinstance(parsed_json.get("answer_draft"), dict):
                parsed_json = parsed_json["answer_draft"]

        return response_model.model_validate(parsed_json)

    except (ValidationError, json.JSONDecodeError, ValueError):
        logger.exception(
            "Gemini returned invalid JSON or failed local validation."
        )
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

    prompt = (
        f"{PLANNER_PROMPT}\n\n"
        f"User question:\n{question}"
    )

    plan = _generate_json(prompt, RetrievalPlan)

    plan.sources = list(dict.fromkeys(plan.sources))

    plan.search_terms = [
        term.strip()
        for term in plan.search_terms
        if isinstance(term, str) and term.strip()
    ][:6]

    plan.rag_query = plan.rag_query.strip()

    if plan.structured_queries:
        plan.structured_query = None

    return plan


def _sql_evidence(rows: list[dict]) -> list[dict]:

    evidence = []

    for index, row in enumerate(rows, start=1):
        evidence.append(
            {
                "evidence_id": f"SQL-{index}",
                "source": "sql",
                "source_reference": {
                    "file_name": row.get("file_name"),
                    "sheet_name": row.get("sheet_name"),
                    "record_id": row.get("record_id", row.get("id")),
                },
                "content": row,
            }
        )

    return evidence


def _structured_sql_evidence(
    result: dict,
    plan,
    start_index: int = 1,
) -> list[dict]:

    operation = plan.operation
    results = result.get("results") or []

    if not results and operation not in {"count", "sum"}:
        return []

    return [
        {
            "evidence_id": f"SQL-{start_index}",
            "source": "sql",
            "source_reference": {
                "file_name": plan.source_file,
                "sheet": plan.sheet,
                "operation": operation,
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
                    "chunk_id": chunk.get("chunk_id"),
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


def _validate_citations(
    answer: str,
    evidence: list[dict],
) -> tuple[bool, list[str]]:
    """
    Validate citations, including multiple IDs inside one bracket.

    Supported:
        [SQL-1]
        [RAG-1, RAG-2]
        [SQL-1, RAG-1]
    """

    valid_ids = {
        item["evidence_id"]
        for item in evidence
        if item.get("evidence_id")
    }

    cited_ids = re.findall(
        r"\b(?:SQL|RAG)-\d+\b",
        answer,
    )

    if not cited_ids:
        return False, []

    invalid_ids = sorted(set(cited_ids) - valid_ids)

    return not invalid_ids, invalid_ids


def _confidence(
    sql_count: int,
    rag_count: int,
    conflicts: list[str],
    limitations: list[str],
    citation_validation_failed: bool = False,
) -> ConfidenceAssessment:
    """Estimate confidence without treating all retrieved evidence equally."""

    if citation_validation_failed:
        return ConfidenceAssessment(
            level="low",
            rationale=(
                "The generated answer failed evidence citation validation."
            ),
        )

    if conflicts:
        return ConfidenceAssessment(
            level="low",
            rationale=(
                "The retrieved evidence contains conflicting information."
            ),
        )

    if limitations:
        return ConfidenceAssessment(
            level="low",
            rationale=(
                "One or more retrieval limitations were detected. "
                "The answer may not cover all requested information."
            ),
        )

    if sql_count > 0 and rag_count > 0:
        return ConfidenceAssessment(
            level="high",
            rationale=(
                "Both structured and document evidence were retrieved "
                "without reported retrieval limitations. Citation "
                "references were validated."
            ),
        )

    if sql_count > 0 or rag_count > 0:
        return ConfidenceAssessment(
            level="moderate",
            rationale=(
                "Supporting evidence was retrieved from at least one "
                "source and citation references were validated."
            ),
        )

    return ConfidenceAssessment(
        level="low",
        rationale="No supporting evidence was retrieved.",
    )


def _extract_structured_record_field(row: dict, field_name: str):
    """Read a source column from an extracted_record row safely."""
    extracted = row.get("extracted_data")

    if isinstance(extracted, str):
        try:
            extracted = json.loads(extracted)
        except json.JSONDecodeError:
            return None

    if not isinstance(extracted, dict):
        return None

    data = extracted.get("data", extracted)
    if not isinstance(data, dict):
        return None

    value = data.get(field_name)
    if value is None:
        # Be tolerant of harmless whitespace/case differences in source keys.
        wanted = field_name.strip().casefold()
        for key, candidate in data.items():
            if isinstance(key, str) and key.strip().casefold() == wanted:
                value = candidate
                break

    if isinstance(value, str):
        value = value.strip()

    return value if value not in (None, "") else None


def _is_employee_manager_question(question: str) -> bool:
    """Identify questions that require resolving an employee's manager."""
    normalized = question.casefold()
    patterns = (
        r"\breport(?:s|ing)?\s+to\b",
        r"\bwho\s+is\s+.{0,80}\bmanager\b",
        r"\bmanager\s+of\b",
        r"\bwho\s+does\s+.{0,80}\breport\s+to\b",
    )
    return any(re.search(pattern, normalized) for pattern in patterns)


def _build_manager_lookup(manager_id: str) -> StructuredQueryPlan:
    """Build a validated second-stage lookup from a retrieved Manager ID."""
    return StructuredQueryPlan(
        source_file="Employee_Master.xlsx",
        sheet="Employees",
        operation="search",
        filters=[
            {
                "field": "Emp ID",
                "operator": "equals",
                "value": manager_id,
            }
        ],
        limit=1,
    )


def answer_question(question: str) -> AgentResponse:

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    plan = _plan(question)

    evidence = []
    limitations = []

    sql_count = 0
    rag_count = 0

    # ---------------------------------------------------------
    # STRUCTURED SQL RETRIEVAL
    # ---------------------------------------------------------

    if "sql" in plan.sources:

        structured_queries = list(plan.structured_queries)

        if not structured_queries and plan.structured_query is not None:
            structured_queries = [plan.structured_query]

        if structured_queries:

            for query_index, query_plan in enumerate(
                structured_queries,
                start=1,
            ):

                try:
                    logger.info(
                        "Executing structured query | index=%d | "
                        "source=%s | sheet=%s | operation=%s",
                        query_index,
                        query_plan.source_file,
                        query_plan.sheet,
                        query_plan.operation,
                    )

                    result = execute_structured_query(
                        query_plan.model_dump()
                    )

                    sql_items = _structured_sql_evidence(
                        result,
                        query_plan,
                        start_index=sql_count + 1,
                    )

                    evidence.extend(sql_items)
                    sql_count += len(sql_items)

                    # Resolve employee-manager relationships in two stages.
                    # The manager ID must come from the employee record returned
                    # by SQL; it is never guessed by the language model.
                    is_employee_lookup = (
                        query_plan.source_file == "Employee_Master.xlsx"
                        and query_plan.sheet == "Employees"
                        and query_plan.operation == "search"
                    )
                    if (
                        is_employee_lookup
                        and _is_employee_manager_question(question)
                        and result.get("results")
                    ):
                        for employee_row in result["results"]:
                            manager_id = _extract_structured_record_field(
                                employee_row, "Manager ID"
                            )
                            if not manager_id:
                                limitations.append(
                                    "The employee record did not contain a Manager ID, "
                                    "so the manager could not be resolved."
                                )
                                continue

                            manager_plan = _build_manager_lookup(str(manager_id))
                            logger.info(
                                "Executing dependent manager lookup | manager_id=%s",
                                manager_id,
                            )
                            try:
                                manager_result = execute_structured_query(
                                    manager_plan.model_dump()
                                )
                                manager_items = _structured_sql_evidence(
                                    manager_result,
                                    manager_plan,
                                    start_index=sql_count + 1,
                                )
                                evidence.extend(manager_items)
                                sql_count += len(manager_items)

                                if not manager_items:
                                    limitations.append(
                                        "The manager ID was found, but no matching "
                                        "manager employee record was found."
                                    )
                                if manager_result.get("truncated"):
                                    limitations.append(
                                        "The manager lookup results were truncated."
                                    )
                            except Exception:
                                logger.exception(
                                    "Dependent manager lookup failed | manager_id=%s",
                                    manager_id,
                                )
                                limitations.append(
                                    "The manager employee record could not be retrieved."
                                )

                    if result.get("truncated"):
                        limitations.append(
                            "Structured SQL results were truncated for "
                            f"{query_plan.source_file} / {query_plan.sheet}."
                        )

                    if not sql_items:
                        limitations.append(
                            "No matching records were found in "
                            f"{query_plan.source_file} / {query_plan.sheet}."
                        )

                except Exception:
                    logger.exception(
                        "Structured query failed | source=%s | sheet=%s",
                        query_plan.source_file,
                        query_plan.sheet,
                    )

                    limitations.append(
                        "Structured query failed for "
                        f"{query_plan.source_file} / {query_plan.sheet}."
                    )

        else:
            try:
                rows = search_structured_records(plan.search_terms)

                sql_items = _sql_evidence(rows)

                evidence.extend(sql_items)
                sql_count += len(sql_items)

                if not rows:
                    limitations.append(
                        "No matching structured records were found."
                    )

            except Exception:
                logger.exception("Generic structured record retrieval failed.")

                limitations.append(
                    "Structured record retrieval was unavailable."
                )

    # ---------------------------------------------------------
    # RAG RETRIEVAL
    # ---------------------------------------------------------

    if "rag" in plan.sources:

        try:
            rag_query = plan.rag_query.strip() or question

            chunks = retrieve_relevant_chunks(
                rag_query,
                top_k=5,
            )

            rag_items = _rag_evidence(
                chunks,
                start_index=1,
            )

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
    # NO EVIDENCE
    # ---------------------------------------------------------

    if not evidence:
        retrieval_failed = any(
            limitation in {
                "Structured record retrieval was unavailable.",
                "Document retrieval was unavailable.",
            }
            for limitation in limitations
        )

        if retrieval_failed:
            final_limitations = list(dict.fromkeys(limitations))
        else:
            final_limitations = [
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
            limitations=final_limitations,
        )

    # ---------------------------------------------------------
    # ANSWER GENERATION
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
    # CITATION VALIDATION
    # ---------------------------------------------------------

    citations_valid, invalid_citations = _validate_citations(
        answer_draft.answer,
        evidence,
    )

    citation_validation_failed = not citations_valid

    if citation_validation_failed:

        logger.warning(
            "Answer contains missing or invalid citations: %s",
            invalid_citations,
        )

        limitations.append(
            "The generated answer did not contain valid, "
            "verifiable evidence citations."
        )

        answer_text = (
            "I could not generate an answer with valid evidence "
            "citations. Please refine the question or review "
            "the retrieved evidence."
        )

    else:
        # Citations are validated above and remain available in evidence.
        # Keep the answer field clean for display.
        answer_text = re.sub(
            r"\s*\[(?:(?:SQL|RAG)-\d+(?:\s*,\s*)?)+\]",
            "",
            answer_draft.answer,
        ).strip()

    # ---------------------------------------------------------
    # CONFLICT REPORTING
    # ---------------------------------------------------------

    if answer_draft.conflicts:
        limitations.extend(
            f"Conflicting evidence: {conflict}"
            for conflict in answer_draft.conflicts
        )

    all_limitations = list(
        dict.fromkeys(
            limitations + answer_draft.limitations
        )
    )

    # ---------------------------------------------------------
    # CONFIDENCE
    # ---------------------------------------------------------

    confidence = _confidence(
        sql_count=sql_count,
        rag_count=rag_count,
        conflicts=answer_draft.conflicts,
        limitations=all_limitations,
        citation_validation_failed=citation_validation_failed,
    )

    # ---------------------------------------------------------
    # FINAL RESPONSE
    # ---------------------------------------------------------

    retrieval_sources = []

    if sql_count > 0:
        retrieval_sources.append("sql")

    if rag_count > 0:
        retrieval_sources.append("rag")

    return AgentResponse(
        question=question,
        answer=answer_text,
        retrieval_sources=retrieval_sources,
        evidence=evidence,
        confidence=confidence,
        limitations=all_limitations,
    )