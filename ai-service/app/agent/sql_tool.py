"""Controlled, read-only querying over structured company records."""

from datetime import date, datetime
from typing import Any

from app.rag.vector_store import get_connection


MAX_RESULTS = 25
MAX_TERMS = 6
MAX_TERM_LENGTH = 100
STATEMENT_TIMEOUT_MS = 5000


# Only these source files and their corresponding sheets are queryable.
# Sheet names are represented by the prefix of record_key.
SOURCE_SCHEMAS = {
    "Employee_Master.xlsx": {
        "sheet": "Employees",
        "fields": {
            "Department", "Emp ID", "Exit Date", "Full Name",
            "Join Date", "Location", "Manager ID", "Status",
            "Title", "Work Email",
        },
    },
    "Hiring_Tracker.xlsx": {
        "sheet": "Requisitions",
        "fields": {
            "Role", "Team", "Notes", "Opened", "Req ID",
            "Status", "Status Date", "In pipeline", "Hiring Manager",
        },
    },
    "Jira_Export_ATLAS.xlsx": {
        "sheets": {
            "Issues": {
                "fields": {
                    "Assignee", "Created", "Epic Link", "Key",
                    "Last Changed", "Resolved", "Status",
                    "Story Points", "Summary", "Type",
                },
            },
            "Epics": {
                "fields": {"Epic Link", "Epic Name"},
            },
            "Versions": {
                "fields": {
                    "Version", "Changed By", "Last Changed",
                    "Release Date", "Original Release Date",
                },
            },
        },
    },
    "Incidents_Aug-Oct_2026.xlsx": {
        "sheet": "Incidents",
        "fields": {
            "ID", "Opened", "Resolved", "Responder",
            "Service", "Severity",
        },
    },
    "Payroll_Register_Jan-Mar_2026.xlsx": {
        "sheet": "Payroll Q4",
        "fields": {
            "Days in Month", "Days Payable", "Deductions (Rs.)",
            "Emp ID", "Gross (Rs.)", "Month", "Name",
            "Net (Rs.)", "Processed By",
        },
    },
    "Leave_Register.xlsx": {
        "sheet": "Leave",
        "fields": {
            "Approved By", "Days", "Employee", "From",
            "Leave Type", "To",
        },
    },
    "OnCall_Rota.xlsx": {
        "sheet": "OnCall Rota",
        "fields": {"Primary", "Secondary", "Week of"},
    },
    "Pulse_Survey.xlsx": {
        "sheet": "Pulse Survey",
        "fields": {
            "Comments", "Engagement (1-5)", "Quarter",
            "Responses", "Team", "Team size",
        },
    },
    "GL_Export_Apr-Sep_2026.xlsx": {
        "sheet": "GL",
        "fields": {
            "Amount (Rs.)", "Cost Centre", "Entered By",
            "Narration", "Ref", "Txn Date", "Vendor / Payee",
            "Voucher",
        },
    },
    "Evidence_Index.xlsx": {
        "sheet": "Evidence Index",
        "fields": {
            "Confidence (H/M/L)", "Date (as written)",
            "Date (normalised, IST)", "Entities named",
            "Fact (your words)", "File", "Ref",
            "Sheet / page / row",
        },
    },
}


ALLOWED_OPERATIONS = {
    "search",
    "count",
    "group_count",
    "sum",
    "group_sum",
}


def _json_safe(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, dict):
        return {
            str(key): _json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]

    return value


def _validate_source(source_file: str, sheet: str) -> set[str]:
    schema = SOURCE_SCHEMAS.get(source_file)

    if not schema:
        raise ValueError("Unsupported structured source file.")

    if "sheets" in schema:
        sheet_schema = schema["sheets"].get(sheet)

        if not sheet_schema:
            raise ValueError("Unsupported sheet for the selected source file.")
    else:
        if schema["sheet"] != sheet:
            raise ValueError("Unsupported sheet for the selected source file.")

        sheet_schema = schema

    return sheet_schema["fields"]


def _validate_field(field: str, allowed_fields: set[str]) -> None:
    if not isinstance(field, str) or field not in allowed_fields:
        raise ValueError(f"Unsupported structured field: {field}")


def _validate_filters(filters: list[dict], allowed_fields: set[str]) -> None:
    if not isinstance(filters, list) or len(filters) > 10:
        raise ValueError("Filters must be a list containing at most 10 items.")

    for item in filters:
        if not isinstance(item, dict):
            raise ValueError("Each filter must be an object.")

        _validate_field(item.get("field"), allowed_fields)

        if item.get("operator") not in {"equals", "contains"}:
            raise ValueError("Unsupported filter operator.")

        value = item.get("value")

        if not isinstance(value, (str, int, float)):
            raise ValueError("Filter values must be text or numbers.")

        if len(str(value)) > MAX_TERM_LENGTH:
            raise ValueError("Filter value is too long.")


def _numeric_expression() -> str:
    """Safely convert numeric JSON values; invalid values become NULL."""
    value = "(r.extracted_data->'data'->>%s)"

    return (
        f"CASE WHEN {value} ~ '^-?[0-9]+([.][0-9]+)?$' "
        f"THEN ({value})::numeric ELSE NULL END"
    )


def _execute_query(sql: str, params: tuple) -> list[dict]:
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("SET TRANSACTION READ ONLY")
            cursor.execute(
                "SELECT set_config('statement_timeout', %s, true)",
                (f"{STATEMENT_TIMEOUT_MS}ms",),
            )

            cursor.execute(sql, params)

            columns = [
                description.name
                for description in cursor.description
            ]
            rows = cursor.fetchall()

        connection.rollback()

        return [
            _json_safe(dict(zip(columns, row)))
            for row in rows
        ]

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def execute_structured_query(plan: dict) -> dict:
    """Execute a validated structured query using approved SQL operations."""

    if not isinstance(plan, dict):
        raise ValueError("Query plan must be an object.")

    source_file = plan.get("source_file")
    sheet = plan.get("sheet")
    operation = plan.get("operation")

    if operation not in ALLOWED_OPERATIONS:
        raise ValueError("Unsupported structured query operation.")

    allowed_fields = _validate_source(source_file, sheet)

    filters = plan.get("filters", [])
    _validate_filters(filters, allowed_fields)

    field = plan.get("field")
    group_by = plan.get("group_by")

    if operation in {"sum", "group_sum"}:
        _validate_field(field, allowed_fields)

    if operation in {"group_count", "group_sum"}:
        _validate_field(group_by, allowed_fields)

    if operation == "sum" and field is None:
        raise ValueError("A field is required for sum operations.")

    if operation == "group_sum" and field == group_by:
        raise ValueError("The grouping and aggregation fields must differ.")

    params = [source_file, f"{sheet}:%"]

    where_clauses = [
        "r.extraction_status = 'SUCCESS'",
        "f.file_name = %s",
        "r.record_key LIKE %s",
    ]

    for item in filters:
        field_name = item["field"]
        value = item["value"]

        expression = "r.extracted_data->'data'->>%s"
        params.append(field_name)

        if item["operator"] == "equals":
            where_clauses.append(f"{expression} = %s")
            params.append(str(value))
        else:
            where_clauses.append(f"{expression} ILIKE %s")
            params.append(f"%{value}%")

    base = """
        FROM extracted_record AS r
        JOIN ingestion_file AS f ON f.id = r.ingestion_file_id
        WHERE
    """

    where_sql = " AND ".join(where_clauses)

    if operation == "search":
        limit = plan.get("limit", MAX_RESULTS)

        if not isinstance(limit, int) or not 1 <= limit <= MAX_RESULTS:
            raise ValueError(
                f"Search limit must be between 1 and {MAX_RESULTS}."
            )

        sql = f"""
            SELECT r.id, r.record_type, r.record_key,
                   r.source_locator, r.extracted_data,
                   r.confidence_score, f.file_name, f.relative_path
            {base} {where_sql}
            ORDER BY r.created_at DESC
            LIMIT %s
        """

        rows = _execute_query(sql, tuple(params + [limit + 1]))

        truncated = len(rows) > limit
        rows = rows[:limit]

        return {
            "operation": operation,
            "results": rows,
            "result_count": len(rows),
            "truncated": truncated,
        }

    if operation == "count":
        sql = f"""
            SELECT COUNT(*) AS total_count
            {base} {where_sql}
        """

        rows = _execute_query(sql, tuple(params))

        return {
            "operation": operation,
            "results": rows,
            "truncated": False,
        }

    if operation == "group_count":
        sql = f"""
            SELECT r.extracted_data->'data'->>%s AS group_value,
                   COUNT(*) AS total_count
            {base} {where_sql}
            GROUP BY group_value
            ORDER BY total_count DESC
        """

        rows = _execute_query(sql, tuple([group_by] + params))

        return {
            "operation": operation,
            "results": rows,
            "truncated": False,
        }

    numeric_sql = _numeric_expression()

    if operation == "sum":
        sql = f"""
            SELECT SUM({numeric_sql}) AS total_sum,
                   COUNT(*) AS matched_records,
                   COUNT({numeric_sql}) AS numeric_records
            {base} {where_sql}
        """

        # numeric_sql appears twice, with two placeholders each.
        numeric_params = [field, field, field, field]

        rows = _execute_query(
            sql,
            tuple(numeric_params + params),
        )

        return {
            "operation": operation,
            "results": rows,
            "truncated": False,
        }

    if operation == "group_sum":
        sql = f"""
            SELECT r.extracted_data->'data'->>%s AS group_value,
                   SUM({numeric_sql}) AS total_sum,
                   COUNT(*) AS matched_records,
                   COUNT({numeric_sql}) AS numeric_records
            {base} {where_sql}
            GROUP BY group_value
            ORDER BY total_sum DESC NULLS LAST
        """

        # One placeholder for group_by, plus four for numeric_sql.
        query_params = [group_by, field, field, field, field] + params

        rows = _execute_query(
            sql,
            tuple(query_params),
        )

        return {
            "operation": operation,
            "results": rows,
            "truncated": False,
        }


def search_structured_records(
    search_terms: list[str],
    limit: int = MAX_RESULTS,
) -> list[dict]:
    """Backward-compatible generic search used by the existing orchestrator."""

    if not isinstance(search_terms, list):
        raise ValueError("Search terms must be a list of strings.")

    terms = [
        term.strip()
        for term in search_terms
        if isinstance(term, str) and term.strip()
    ]

    if not terms:
        return []

    if len(terms) > MAX_TERMS or any(
        len(term) > MAX_TERM_LENGTH for term in terms
    ):
        raise ValueError("Invalid search terms.")

    if not isinstance(limit, int) or not 1 <= limit <= MAX_RESULTS:
        raise ValueError(
            f"Result limit must be between 1 and {MAX_RESULTS}."
        )

    patterns = [f"%{term}%" for term in terms]

    sql = """
        SELECT r.id, r.record_type, r.record_key,
               r.source_locator, r.extracted_data,
               r.extraction_method, r.confidence_score,
               r.created_at, f.file_name, f.relative_path,
               f.file_type
        FROM extracted_record AS r
        JOIN ingestion_file AS f ON f.id = r.ingestion_file_id
        WHERE r.extraction_status = 'SUCCESS'
          AND (
              r.extracted_data::text ILIKE ANY (%s)
              OR r.record_key ILIKE ANY (%s)
              OR f.file_name ILIKE ANY (%s)
          )
        ORDER BY r.created_at DESC
        LIMIT %s
    """

    rows = _execute_query(
        sql,
        (patterns, patterns, patterns, limit + 1),
    )

    return rows[:limit]
