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
    discover_structured_catalogue,
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
You are the retrieval-planning brain of Veloxa CXO Cockpit, an AI assistant
that answers questions from the company's ingested data. Your job is to
understand the user's intent and create the smallest complete retrieval plan.
Do not answer the question yourself.

AVAILABLE DATA SOURCES
- sql: structured records extracted from spreadsheets, CSVs and other tabular data.
- rag: document chunks extracted from PDFs, Word files, emails, transcripts and notes.

A LIVE STRUCTURED CATALOGUE is appended below this prompt. It is the source of
truth for available files, sheets, fields and observed data types. The catalogue
can change whenever new files are ingested. Never rely on remembered filenames,
schemas or company-specific assumptions. Never invent a source, sheet or field.

SOURCE SELECTION
1. Use SQL for exact values, entity lookups, row details, counts, totals,
   grouped summaries, statuses, dates, rankings and comparisons available in
   structured fields.
2. Use RAG for narrative explanations, decisions, policies, meeting context,
   email content, transcript statements and facts that exist only in documents.
3. Use both when the question asks to connect structured facts with narrative
   context, verify a structured fact against a document, or compare information
   across tabular and unstructured sources.
4. If the question is broad or its source is uncertain, use the available
   catalogue to select relevant SQL sources and use RAG for contextual evidence.
5. Do not select a source merely because its name looks relevant. Match the
   meaning of the question to the actual fields and document content likely to
   contain the answer.

SQL QUERY DESIGN
- Use exact source_file, sheet and field names from the live catalogue.
- Use search to retrieve matching records and their available fields. Prefer
  search for questions about a named person, project, transaction, issue,
  requisition, event or other individual entity.
- Use count for a total number of matching records.
- Use group_count for counts broken down by a field.
- Use sum for a numeric total and group_sum for numeric totals grouped by a field.
- Use equals for exact matches, contains for partial text matches, and in for
  matching any of several exact values.
- Use filters only when supported by the question. Do not invent filter values.
- For a comparison, retrieve each required period/category separately or use a
  grouped operation if one query can faithfully answer it.
- For multi-part questions, create multiple structured_queries, one for each
  distinct source/sheet/aggregation needed. The maximum is 10.
- When the user asks for a breakdown and an overall total, plan both; do not
  assume the grouped rows alone are the requested grand total.
- For questions involving relationships between records, retrieve the primary
  record and the referenced record when the catalogue exposes the linking key.
  A referenced ID is not a human-readable name; resolve it from another record.
- For numeric calculations, use the numeric field shown in the catalogue. Do
  not sum identifier, date, descriptive or categorical fields.
- Do not create duplicate queries. Do not request fields that are absent.
- Set search limit to at most 25.

RAG QUERY DESIGN
- Write one concise, semantically rich rag_query that preserves the entities,
  dates, topic and intent from the user's question.
- For a question about a named event, decision or meeting, include its likely
  date and key entities when supplied by the user.
- Use RAG alongside SQL when documentary context could materially change or
  qualify the answer. Do not use RAG as a substitute for exact SQL arithmetic.

GENERAL RULES
- Prefer a complete, focused plan over many speculative queries.
- If no matching structured source or field exists, do not fabricate one; use
  RAG if documents could contain the answer.
- If neither source is suitable, return an empty plan rather than guessing.
- Return only valid JSON matching RetrievalPlan. Use only these fields:
  sources, search_terms, rag_query, structured_query, structured_queries.
"""


ANSWER_PROMPT = """
You are Veloxa CXO Cockpit, an evidence-grounded AI assistant. Answer the user's
question using only the retrieved evidence supplied below. The user expects a
clear, useful answer—not a description of the retrieval process.

ANSWER QUALITY
1. Answer the actual question directly in the first sentence.
2. Address every part of a multi-part question. Use short headings or bullets
   when they make a multi-part answer easier to read.
3. Include relevant names, dates, amounts, units, statuses, counts and context
   present in the evidence. Do not omit a requested breakdown when it is present.
4. For comparisons, show both sides and state the direction and size of change
   only when those values can be calculated from the evidence.
5. Distinguish source facts from derived calculations. Show the calculation
   briefly when it helps verify a total, percentage or difference.
6. Preserve the source's exact meaning, period labels, units and status wording.
   Do not relabel quarters or infer a reporting period.
7. Resolve IDs to human-readable names only when another supplied evidence item
   supports the mapping. Never guess a person's identity or relationship.
8. If evidence from different sources refers to different dates or snapshots,
   explain the timing rather than silently treating them as simultaneous.

EVIDENCE AND SAFETY
9. Every factual claim must cite one or more exact evidence IDs from the supplied
   evidence, using [SQL-1], [RAG-1] or [SQL-1, RAG-1].
10. Never invent, alter or guess evidence IDs, facts, figures, names or dates.
11. Use SQL evidence for exact structured values and calculations; use RAG
    evidence for statements, explanations and documentary context. Combine them
    when the question requires both.
12. If sources disagree, state the competing facts, identify their sources and
    dates where available, and add a conflict. Do not choose a winner without
    evidence that establishes which source is authoritative or newer.
13. If a requested field or fact is absent, explicitly say it cannot be determined
    from the available evidence. Do not infer it from a nearby field.
14. If a result is truncated or only a partial set is available, disclose that
    limitation and do not present it as a complete population.
15. Do not claim a document, row, period or source was checked unless it appears
    in the supplied evidence.
16. Keep the answer concise but sufficiently detailed to satisfy the question.
    Avoid generic filler, unnecessary disclaimers and unsupported advice.

Return only valid JSON matching AnswerDraft with these fields:
- answer: the user-facing answer with inline evidence citations.
- conflicts: material disagreements between supplied evidence items, or [].
- limitations: missing information or retrieval limitations relevant to the
  question, or [].
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



def _normalize_retrieval_plan(parsed_json) -> dict:
    """
    Convert common Gemini/Groq planner response variations into the
    canonical RetrievalPlan shape. This only renames/repackages information;
    it never invents a source file, sheet, operation, field, or filter value.
    """
    if isinstance(parsed_json, list):
        data = {"structured_queries": parsed_json}
    elif isinstance(parsed_json, dict):
        data = dict(parsed_json)
    else:
        raise ValueError("Planner response must be a JSON object or query list.")

    # Unwrap known planner wrappers.
    for wrapper in ("retrieval_plan", "plan", "query_plan"):
        nested = data.get(wrapper)
        if isinstance(nested, dict):
            data = dict(nested)
            break
        if isinstance(nested, list):
            data = {"structured_queries": nested}
            break

    # Provider-specific names used for source declarations.
    if "sources" not in data:
        for alias in ("target_sources", "selected_sources", "sources_to_consult"):
            if data.get(alias) is not None:
                data["sources"] = data[alias]
                break
    if "source" not in data and data.get("source_type") is not None:
        data["source"] = data["source_type"]

    # Some models return a list under a generic `queries` key.
    if not data.get("structured_queries"):
        for alias in ("queries", "query_plans", "sql_queries"):
            if isinstance(data.get(alias), list):
                data["structured_queries"] = data[alias]
                break

    # Normalize source declarations. Source objects may also contain queries.
    raw_sources = data.get("sources", data.get("target_sources"))
    if raw_sources is None:
        raw_sources = data.get("source", [])

    if isinstance(raw_sources, str):
        raw_sources = [raw_sources]
    elif not isinstance(raw_sources, list):
        raw_sources = []

    normalized_sources = []
    queries = data.get("structured_queries") or []
    if isinstance(queries, dict):
        queries = [queries]
    else:
        queries = list(queries) if isinstance(queries, list) else []

    for source_item in raw_sources:
        if isinstance(source_item, str):
            if source_item.lower() in {"sql", "rag"}:
                normalized_sources.append(source_item.lower())
            continue
        if not isinstance(source_item, dict):
            continue

        declared_type = (
            source_item.get("type")
            or source_item.get("source_type")
        )
        source_value = source_item.get("source")
        source_type = declared_type or (
            source_value if isinstance(source_value, str)
            and source_value.lower() in {"sql", "rag"} else None
        )
        if isinstance(source_type, str) and source_type.lower() in {"sql", "rag"}:
            source_type = source_type.lower()
            normalized_sources.append(source_type)

        nested_queries = (
            source_item.get("structured_queries")
            or source_item.get("queries")
            or []
        )
        if isinstance(nested_queries, dict):
            nested_queries = [nested_queries]

        if source_type == "rag":
            # A RAG source's query is a retrieval phrase, not a SQL query plan.
            rag_value = (
                source_item.get("rag_query")
                or source_item.get("search_query")
                or source_item.get("query")
            )
            if isinstance(rag_value, str) and rag_value.strip():
                existing_rag = data.get("rag_query") or data.get("rag_queries") or ""
                if isinstance(existing_rag, list):
                    existing_rag = " ".join(str(x) for x in existing_rag if x)
                data["rag_query"] = " ".join(
                    part for part in (str(existing_rag).strip(), rag_value.strip()) if part
                )
        elif isinstance(nested_queries, list):
            for item in nested_queries:
                if isinstance(item, dict):
                    item = dict(item)
                    inherited_file = (
                        source_item.get("source_file")
                        or source_item.get("file")
                        or (
                            source_value
                            if isinstance(source_value, str)
                            and source_value.lower() not in {"sql", "rag"}
                            else None
                        )
                    )
                    item.setdefault("source_file", inherited_file)
                    item.setdefault("sheet", source_item.get("sheet") or source_item.get("sheet_name"))
                    queries.append(item)

        if source_type == "sql" and source_item.get("operation") and not nested_queries:
            item = dict(source_item)
            for key in ("type", "source_type", "source"):
                item.pop(key, None)
            queries.append(item)

    # A top-level object can itself be one structured query.
    if data.get("operation") and not queries:
        top_level_query = dict(data)
        if (
            top_level_query.get("source_file") is None
            and isinstance(top_level_query.get("source"), str)
            and top_level_query["source"].lower() not in {"sql", "rag"}
        ):
            top_level_query["source_file"] = top_level_query["source"]
        queries = [top_level_query]

    def normalize_filter_list(filters):
        if filters is None:
            return []
        if isinstance(filters, list):
            result = []
            for item in filters:
                if not isinstance(item, dict):
                    continue
                field = item.get("field") or item.get("column")
                operator = item.get("operator") or item.get("op") or "equals"
                operator = str(operator).strip().lower()
                operator = {"eq": "equals", "=": "equals", "like": "contains", "range": "between"}.get(operator, operator)
                value = item.get("value")
                if field and value is not None:
                    result.append({"field": field, "operator": operator, "value": value})
            return result
        if isinstance(filters, dict):
            result = []
            for field, condition in filters.items():
                if isinstance(condition, dict):
                    if "value" in condition:
                        value = condition["value"]
                        operator = condition.get("operator") or condition.get("op") or "equals"
                        operator = str(operator).strip().lower()
                        operator = {"eq": "equals", "=": "equals", "like": "contains", "range": "between"}.get(operator, operator)
                    elif len(condition) == 1:
                        operator, value = next(iter(condition.items()))
                        operator = str(operator).strip().lower()
                        operator = {"eq": "equals", "=": "equals", "like": "contains", "range": "between"}.get(operator, operator)
                    else:
                        continue
                else:
                    operator, value = "equals", condition
                if value is not None:
                    result.append({"field": field, "operator": operator, "value": value})
            return result
        return []

    normalized_queries = []
    for raw_query in queries:
        if not isinstance(raw_query, dict):
            continue
        query = dict(raw_query)

        aliases = {
            "sheet": ("sheet_name", "worksheet"),
            "source_file": ("file_name", "filename", "file", "source"),
            "field": ("target_field", "metric_field", "measure", "aggregation_field", "numeric_field", "value_field"),
            "group_by": ("group_by_field", "grouping_field", "group_field", "grouping_field_name"),
            "operation": ("aggregation", "query_type", "action"),
        }
        for canonical, alternatives in aliases.items():
            if query.get(canonical) is None:
                for alias in alternatives:
                    if query.get(alias) is not None:
                        query[canonical] = query[alias]
                        break

        # `fields` is accepted only when it unambiguously names one field.
        if query.get("field") is None:
            fields = query.get("fields")
            if isinstance(fields, str):
                query["field"] = fields
            elif isinstance(fields, list) and len(fields) == 1 and isinstance(fields[0], str):
                query["field"] = fields[0]

        # Some providers return a one-element grouping list for a scalar field.
        # It is safe to unwrap only that unambiguous case.
        group_by = query.get("group_by")
        if isinstance(group_by, list) and len(group_by) == 1 and isinstance(group_by[0], str):
            query["group_by"] = group_by[0]

        # Do not treat source-type labels as filenames.
        if isinstance(query.get("source_file"), str) and query["source_file"].lower() in {"sql", "rag"}:
            query.pop("source_file")

        # Providers sometimes emit null optional values. Restore safe defaults.
        if query.get("limit") is None:
            query["limit"] = 25
        # A source+sheet with no operation is an entity/row lookup by default.
        # This does not infer a metric or aggregation field.
        if not query.get("operation"):
            query["operation"] = "search"
        query["filters"] = normalize_filter_list(query.get("filters"))
        normalized_queries.append(query)

    search_terms = data.get("search_terms")
    if search_terms is None:
        search_terms = data.get("search_queries", data.get("keywords", []))
    if isinstance(search_terms, str):
        search_terms = [search_terms]
    if not isinstance(search_terms, list):
        search_terms = []

    rag_query = data.get("rag_query")
    if rag_query is None:
        rag_query = data.get("rag_queries", data.get("rag_search_terms", ""))
    if isinstance(rag_query, list):
        rag_query = " ".join(str(item) for item in rag_query if item)
    elif not isinstance(rag_query, str):
        rag_query = str(rag_query or "")

    # Validate each query independently. A malformed model-generated query
    # must not turn an otherwise recoverable user request into HTTP 422.
    valid_queries = []
    for query in normalized_queries:
        try:
            valid_queries.append(StructuredQueryPlan.model_validate(query).model_dump())
        except ValidationError as error:
            logger.warning("Dropping invalid planner query; using remaining retrieval paths: %s", error)

    normalized_queries = valid_queries

    structured_query = data.get("structured_query")
    if isinstance(structured_query, dict):
        singular = _normalize_retrieval_plan({
            "sources": ["sql"],
            "structured_queries": [structured_query],
        })
        structured_query = singular["structured_queries"][0] if singular["structured_queries"] else None
    else:
        structured_query = None

    if (normalized_queries or structured_query or search_terms) and "sql" not in normalized_sources:
        normalized_sources.append("sql")
    if rag_query.strip() and "rag" not in normalized_sources:
        normalized_sources.append("rag")

    return {
        "sources": list(dict.fromkeys(normalized_sources)),
        "search_terms": search_terms,
        "rag_query": rag_query,
        "structured_query": structured_query,
        "structured_queries": normalized_queries,
    }


def _normalize_provider_response(parsed_json, response_model: type[BaseModel]) -> dict:
    if response_model is RetrievalPlan:
        return _normalize_retrieval_plan(parsed_json)

    if not isinstance(parsed_json, dict):
        raise ValueError("AI response must be a JSON object.")

    data = dict(parsed_json)
    if response_model is AnswerDraft and isinstance(data.get("answer_draft"), dict):
        data = dict(data["answer_draft"])
    return data


def _normalize_groq_response(
    parsed_json,
    response_model: type[BaseModel],
) -> dict:
    return _normalize_provider_response(parsed_json, response_model)


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

        normalized_json = _normalize_provider_response(
            parsed_json,
            response_model,
        )

        return response_model.model_validate(normalized_json)

    except (ValidationError, json.JSONDecodeError, ValueError):
        logger.exception(
            "Gemini returned invalid JSON or failed local validation."
        )
        if response_model is RetrievalPlan and groq_client is not None:
            logger.warning(
                "Gemini planner output was invalid. Attempting Groq planner fallback."
            )
            try:
                return _generate_with_groq(prompt, response_model)
            except Exception:
                logger.exception("Groq fallback also failed after invalid Gemini planner output.")
                raise
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
    try:
        catalogue = discover_structured_catalogue()
    except Exception:
        logger.exception("Dynamic structured catalogue discovery failed.")
        catalogue = {}

    catalogue_lines = []
    for source_file, sheets in sorted(catalogue.items()):
        for sheet_name, details in sorted(sheets.items()):
            fields = details.get("fields", [])
            field_details = details.get("field_details", {})
            descriptions = []
            for field_name in fields:
                observed_type = field_details.get(
                    field_name, {}
                ).get("observed_types", "unknown")
                descriptions.append(
                    f"{field_name} (observed type: {observed_type})"
                )
            catalogue_lines.append(
                f"- Source: {source_file} | Sheet: {sheet_name} | "
                f"Fields: {', '.join(descriptions)}"
            )

    catalogue_text = (
        "\n".join(catalogue_lines)
        if catalogue_lines
        else "No structured records are currently available."
    )
    prompt = (
        f"{PLANNER_PROMPT}\n\n"
        f"LIVE STRUCTURED CATALOGUE\n{catalogue_text}\n\n"
        f"User question:\n{question}"
    )

    plan = _generate_json(prompt, RetrievalPlan)
    plan.sources = list(dict.fromkeys(plan.sources))
    plan.search_terms = [
        term.strip()
        for term in plan.search_terms
        if isinstance(term, str) and term.strip()
    ][:6]
    plan.rag_query = (plan.rag_query or "").strip()

    if plan.structured_queries:
        plan.structured_query = None

    if not catalogue and "sql" in plan.sources:
        plan.sources = [
            source for source in plan.sources if source != "sql"
        ]
        logger.warning(
            "SQL removed from plan because the live catalogue is empty."
        )

    # A valid but empty planner response must not silently terminate retrieval.
    # Fall back to broad, question-led retrieval without assuming any domain,
    # filename, entity type, or schema. SQL is included only when a live
    # structured catalogue exists; RAG is always a safe document-search path.
    if not plan.sources:
        plan.sources = ["rag"]
        if catalogue:
            plan.sources.insert(0, "sql")
        terms = re.findall(r"[\w@.+-]{3,}", question, flags=re.UNICODE)
        plan.search_terms = list(dict.fromkeys(terms))[:6]
        plan.rag_query = question.strip()[:500]
        logger.warning(
            "Planner returned no usable retrieval source; using generic fallback: %s",
            plan.sources,
        )
    elif "rag" in plan.sources and not plan.rag_query:
        plan.rag_query = question.strip()[:500]

    return plan



def _compact_evidence_for_prompt(
    evidence: list[dict],
    max_total_chars: int = 18000,
    max_item_chars: int = 3500,
) -> tuple[list[dict], bool]:
    """Bound model context while preserving evidence IDs and source references."""
    compact = []
    used = 0
    truncated_any = False

    for item in evidence:
        candidate = {
            "evidence_id": item.get("evidence_id"),
            "source": item.get("source"),
            "source_reference": item.get("source_reference", {}),
            "content": item.get("content"),
        }
        if item.get("similarity") is not None:
            candidate["similarity"] = item["similarity"]

        content = candidate.get("content")
        if isinstance(content, dict):
            content = dict(content)
            rows = content.get("results")
            if isinstance(rows, list) and len(rows) > 12:
                content["results"] = rows[:12]
                content["prompt_context_truncated"] = True
                truncated_any = True
            candidate["content"] = content
        elif isinstance(content, str) and len(content) > 2200:
            candidate["content"] = content[:2200] + "…[content truncated for model context]"
            truncated_any = True

        serialized = json.dumps(candidate, ensure_ascii=False, default=str)
        if len(serialized) > max_item_chars:
            # Last-resort bound for unusually large extracted rows/doc chunks.
            candidate["content"] = serialized[:max_item_chars] + "…[evidence shortened]"
            truncated_any = True
            serialized = json.dumps(candidate, ensure_ascii=False, default=str)

        if used + len(serialized) > max_total_chars:
            truncated_any = True
            break

        compact.append(candidate)
        used += len(serialized)

    return compact, truncated_any


def answer_question(question: str) -> AgentResponse:

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    plan = _plan(question)

    evidence = []
    limitations = []

    sql_count = 0
    rag_count = 0
    dependent_lookup_completed = False

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

                                if manager_items and manager_result.get("results"):
                                    dependent_lookup_completed = True

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
                top_k=10,
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

    prompt_evidence, prompt_evidence_truncated = _compact_evidence_for_prompt(evidence)
    if prompt_evidence_truncated:
        limitations.append(
            "Some retrieved evidence was shortened or omitted from the model context to stay within provider limits."
        )

    answer_prompt = (
        f"{ANSWER_PROMPT}\n\n"
        f"User question:\n{question}\n\n"
        f"Retrieved evidence:\n"
        f"{json.dumps(prompt_evidence, ensure_ascii=False, separators=(',', ':'), default=str)}\n\n"
        f"Known limitations:\n"
        f"{json.dumps(limitations, ensure_ascii=False)}"
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

    # One bounded repair attempt: retain the same evidence and require the
    # model to cite only IDs actually present in that evidence.
    if not citations_valid:
        allowed_ids = [
            item["evidence_id"]
            for item in evidence
            if item.get("evidence_id")
        ]
        repair_prompt = (
            f"{answer_prompt}\n\n"
            "CITATION REPAIR REQUIRED. Your previous draft did not pass "
            "citation validation. Rewrite the answer using only the supplied "
            "evidence. Every factual claim must cite one or more exact IDs "
            "from this allowlist. Do not invent, alter, or omit the IDs needed "
            "to support the answer. If evidence is insufficient, say so.\n"
            f"Allowed evidence IDs: {json.dumps(allowed_ids)}\n"
            "Return only valid JSON matching AnswerDraft."
        )
        try:
            repaired_draft = _generate_json(repair_prompt, AnswerDraft)
            repaired_valid, repaired_invalid = _validate_citations(
                repaired_draft.answer,
                evidence,
            )
            if repaired_valid:
                answer_draft = repaired_draft
                citations_valid = True
                invalid_citations = []
            else:
                invalid_citations = repaired_invalid
                logger.warning(
                    "Citation repair attempt also failed validation: %s",
                    repaired_invalid,
                )
        except Exception:
            logger.exception("Citation repair attempt failed.")

    citation_validation_failed = not citations_valid

    if citation_validation_failed:

        logger.warning(
            "Answer contains missing or invalid citations after repair: %s",
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
        dependent_lookup_completed=dependent_lookup_completed,
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
    dependent_lookup_completed: bool = False,
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

    if dependent_lookup_completed:
        return ConfidenceAssessment(
            level="high",
            rationale=(
                "The employee record and the referenced manager record "
                "were both retrieved successfully. The answer citations "
                "were validated, with no reported conflicts or limitations."
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
                "Supporting evidence was retrieved and citation "
                "references were validated, but independent or complete "
                "support for every requested fact has not been established."
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
