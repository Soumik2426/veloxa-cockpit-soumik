"""Controlled, read-only search over the existing structured records."""

from datetime import date, datetime
from typing import Any

from app.rag.vector_store import get_connection


MAX_RESULTS = 25
MAX_TERMS = 6
STATEMENT_TIMEOUT_MS = 3000

# This is the only statement the SQL tool will execute. Identifiers and
# selected columns are fixed; the caller supplies values only as parameters.
STRUCTURED_SEARCH_SQL = """
SELECT r.id,
       r.record_type,
       r.record_key,
       r.source_locator,
       r.extracted_data,
       r.extraction_method,
       r.confidence_score,
       r.created_at,
       f.file_name,
       f.relative_path,
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


def _normalize_sql(sql: str) -> str:
    return " ".join(sql.split()).rstrip(";").lower()


def validate_sql(sql: str) -> None:
    """Reject anything except the single reviewed SELECT template."""
    if not isinstance(sql, str) or ";" in sql.rstrip().rstrip(";"):
        raise ValueError("Only one read-only SELECT statement is permitted.")
    if _normalize_sql(sql) != _normalize_sql(STRUCTURED_SEARCH_SQL):
        raise ValueError("SQL is not an approved structured-record query.")


def _json_safe(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def execute_readonly_sql(sql: str, params: tuple) -> list[dict]:
    """Execute the approved query in a read-only, time-limited transaction."""
    validate_sql(sql)
    if len(params) != 4:
        raise ValueError("Unexpected parameters for structured-record query.")

    patterns, record_patterns, file_patterns, limit = params
    if not all(isinstance(group, (list, tuple)) for group in (patterns, record_patterns, file_patterns)):
        raise ValueError("Search values must be parameterized text lists.")
    if not 1 <= limit <= MAX_RESULTS:
        raise ValueError(f"Result limit must be between 1 and {MAX_RESULTS}.")

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            # Must be the first statement in this transaction.
            cursor.execute("SET TRANSACTION READ ONLY")
            cursor.execute(
                "SELECT set_config('statement_timeout', %s, true)",
                (f"{STATEMENT_TIMEOUT_MS}ms",),
            )
            cursor.execute(sql, params)
            columns = [description.name for description in cursor.description]
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


def search_structured_records(search_terms: list[str], limit: int = MAX_RESULTS) -> list[dict]:
    """Search approved structured record values using bound text terms."""
    if not isinstance(search_terms, list):
        raise ValueError("Search terms must be a list of strings.")
    terms = [term.strip() for term in search_terms if isinstance(term, str) and term.strip()]
    if not terms:
        return []
    if len(terms) > MAX_TERMS or any(len(term) > 100 for term in terms):
        raise ValueError(f"Use at most {MAX_TERMS} search terms, each at most 100 characters.")
    if not 1 <= limit <= MAX_RESULTS:
        raise ValueError(f"Result limit must be between 1 and {MAX_RESULTS}.")

    patterns = [f"%{term}%" for term in terms]
    return execute_readonly_sql(
        STRUCTURED_SEARCH_SQL,
        (patterns, patterns, patterns, limit),
    )
