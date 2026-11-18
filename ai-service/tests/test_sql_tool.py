import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.agent.sql_tool import (
    STRUCTURED_SEARCH_SQL,
    execute_readonly_sql,
    search_structured_records,
)


class FakeCursor:
    def __init__(self):
        self.calls = []
        self.description = [SimpleNamespace(name="id")]

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchall(self):
        return [("record-id",)]


class SQLToolTests(unittest.TestCase):
    def setUp(self):
        self.cursor = FakeCursor()
        self.connection = Mock()
        self.connection.cursor.return_value = self.cursor

    def test_search_runs_only_the_fixed_query_in_read_only_transaction(self):
        with patch("app.agent.sql_tool.get_connection", return_value=self.connection):
            rows = search_structured_records(["engineering", "delivery"])

        self.assertEqual(rows, [{"id": "record-id"}])
        self.assertEqual(self.cursor.calls[0], ("SET TRANSACTION READ ONLY", None))
        self.assertIn("statement_timeout", self.cursor.calls[1][0])
        query, params = self.cursor.calls[2]
        self.assertEqual(query, STRUCTURED_SEARCH_SQL)
        self.assertEqual(params, (["%engineering%", "%delivery%"],) * 3 + (25,))
        self.connection.rollback.assert_called_once()
        self.connection.close.assert_called_once()

    def test_rejects_modifying_and_unapproved_sql(self):
        with patch("app.agent.sql_tool.get_connection") as get_connection:
            for query in (
                "DELETE FROM extracted_record",
                STRUCTURED_SEARCH_SQL + "; DELETE FROM ingestion_file",
                "SELECT * FROM pg_catalog.pg_tables",
            ):
                with self.subTest(query=query[:25]), self.assertRaises(ValueError):
                    execute_readonly_sql(query, ([], [], [], 10))
            get_connection.assert_not_called()

    def test_rejects_invalid_result_limit_before_connecting(self):
        with patch("app.agent.sql_tool.get_connection") as get_connection:
            with self.assertRaises(ValueError):
                search_structured_records(["revenue"], limit=10000)
            get_connection.assert_not_called()

    def test_empty_search_does_not_query_database(self):
        with patch("app.agent.sql_tool.get_connection") as get_connection:
            self.assertEqual(search_structured_records([]), [])
            get_connection.assert_not_called()

    def test_connection_failure_propagates_without_exposing_credentials(self):
        with patch(
            "app.agent.sql_tool.get_connection",
            side_effect=RuntimeError("connection unavailable"),
        ):
            with self.assertRaisesRegex(RuntimeError, "connection unavailable"):
                search_structured_records(["finance"])


if __name__ == "__main__":
    unittest.main()
