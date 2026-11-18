import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.agent.sql_tool import (
    MAX_RESULTS,
    SOURCE_SCHEMAS,
    _execute_query,
    execute_structured_query,
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


class SQLToolTests:

    def setUp(self):
        self.cursor = FakeCursor()
        self.connection = Mock()
        self.connection.cursor.return_value = self.cursor

    # ---------------------------------------------------------
    # Read-only database execution
    # ---------------------------------------------------------

    def test_execute_query_uses_read_only_transaction(self):
        with patch(
            "app.agent.sql_tool.get_connection",
            return_value=self.connection,
        ):
            rows = _execute_query(
                "SELECT id FROM extracted_record",
                (),
            )

        self.assertEqual(rows, [{"id": "record-id"}])

        self.assertEqual(
            self.cursor.calls[0],
            ("SET TRANSACTION READ ONLY", None),
        )

        self.assertIn(
            "statement_timeout",
            self.cursor.calls[1][0],
        )

        self.assertEqual(
            self.cursor.calls[2],
            ("SELECT id FROM extracted_record", ()),
        )

        self.connection.rollback.assert_called_once()
        self.connection.close.assert_called_once()

    def test_connection_is_closed_when_query_fails(self):
        self.cursor.execute = Mock(
            side_effect=RuntimeError("query failed")
        )

        with patch(
            "app.agent.sql_tool.get_connection",
            return_value=self.connection,
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "query failed",
            ):
                _execute_query(
                    "SELECT id FROM extracted_record",
                    (),
                )

        self.connection.rollback.assert_called()
        self.connection.close.assert_called_once()

    def test_connection_failure_propagates(self):
        with patch(
            "app.agent.sql_tool.get_connection",
            side_effect=RuntimeError("connection unavailable"),
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "connection unavailable",
            ):
                _execute_query(
                    "SELECT id FROM extracted_record",
                    (),
                )

    # ---------------------------------------------------------
    # Generic structured record search
    # ---------------------------------------------------------

    def test_search_uses_parameterized_query_and_result_limit(self):
        with patch(
            "app.agent.sql_tool._execute_query",
            return_value=[{"id": "record-id"}],
        ) as execute:

            rows = search_structured_records(
                ["engineering", "delivery"]
            )

        self.assertEqual(rows, [{"id": "record-id"}])

        query, params = execute.call_args.args

        self.assertIn("ILIKE ANY", query)
        self.assertIn("extraction_status = 'SUCCESS'", query)

        self.assertEqual(
            params,
            (
                ["%engineering%", "%delivery%"],
                ["%engineering%", "%delivery%"],
                ["%engineering%", "%delivery%"],
                MAX_RESULTS + 1,
            ),
        )

    def test_search_returns_no_results_for_empty_terms(self):
        with patch(
            "app.agent.sql_tool._execute_query"
        ) as execute:

            rows = search_structured_records([])

        self.assertEqual(rows, [])
        execute.assert_not_called()

    def test_search_rejects_invalid_result_limit(self):
        with patch(
            "app.agent.sql_tool._execute_query"
        ) as execute:

            with self.assertRaises(ValueError):
                search_structured_records(
                    ["revenue"],
                    limit=10000,
                )

        execute.assert_not_called()

    def test_search_rejects_too_many_search_terms(self):
        with patch(
            "app.agent.sql_tool._execute_query"
        ) as execute:

            with self.assertRaises(ValueError):
                search_structured_records(
                    ["term"] * 7
                )

        execute.assert_not_called()

    # ---------------------------------------------------------
    # Structured query validation
    # ---------------------------------------------------------

    def test_supported_source_schemas_are_configured(self):
        self.assertIn(
            "Employee_Master.xlsx",
            SOURCE_SCHEMAS,
        )

        self.assertIn(
            "Jira_Export_ATLAS.xlsx",
            SOURCE_SCHEMAS,
        )

        self.assertEqual(
            SOURCE_SCHEMAS[
                "Payroll_Register_Jan-Mar_2026.xlsx"
            ]["sheet"],
            "Payroll Q4",
        )

    def test_structured_query_rejects_unapproved_source(self):
        with patch(
            "app.agent.sql_tool._execute_query"
        ) as execute:

            with self.assertRaises(ValueError):
                execute_structured_query({
                    "source_file": "unapproved.xlsx",
                    "sheet": "Sheet1",
                    "operation": "count",
                })

        execute.assert_not_called()

    def test_structured_query_rejects_unapproved_field(self):
        with patch(
            "app.agent.sql_tool._execute_query"
        ) as execute:

            with self.assertRaises(ValueError):
                execute_structured_query({
                    "source_file": "Employee_Master.xlsx",
                    "sheet": "Employees",
                    "operation": "group_count",
                    "group_by": "Password",
                })

        execute.assert_not_called()

    def test_structured_query_rejects_unsupported_operation(self):
        with patch(
            "app.agent.sql_tool._execute_query"
        ) as execute:

            with self.assertRaises(ValueError):
                execute_structured_query({
                    "source_file": "Employee_Master.xlsx",
                    "sheet": "Employees",
                    "operation": "delete",
                })

        execute.assert_not_called()

    def test_structured_search_rejects_invalid_limit(self):
        with patch(
            "app.agent.sql_tool._execute_query"
        ) as execute:

            with self.assertRaises(ValueError):
                execute_structured_query({
                    "source_file": "Employee_Master.xlsx",
                    "sheet": "Employees",
                    "operation": "search",
                    "limit": 1000,
                })

        execute.assert_not_called()

    # ---------------------------------------------------------
    # Structured SQL operations
    # ---------------------------------------------------------

    def test_group_sum_builds_parameterized_query(self):
        with patch(
            "app.agent.sql_tool._execute_query",
            return_value=[],
        ) as execute:

            result = execute_structured_query({
                "source_file": "Jira_Export_ATLAS.xlsx",
                "sheet": "Issues",
                "operation": "group_sum",
                "field": "Story Points",
                "group_by": "Status",
                "filters": [
                    {
                        "field": "Type",
                        "operator": "equals",
                        "value": "Story",
                    }
                ],
            })

        self.assertEqual(
            result,
            {
                "operation": "group_sum",
                "results": [],
                "truncated": False,
            },
        )

        query, params = execute.call_args.args

        self.assertIn("GROUP BY group_value", query)
        self.assertIn("ORDER BY total_sum DESC", query)

        self.assertEqual(
            params,
            (
                "Status",
                "Story Points",
                "Story Points",
                "Story Points",
                "Story Points",
                "Jira_Export_ATLAS.xlsx",
                "Issues:%",
                "Type",
                "Story",
            ),
        )

    def test_group_count_supports_multiple_filter_values(self):
        with patch(
            "app.agent.sql_tool._execute_query",
            return_value=[],
        ) as execute:

            execute_structured_query({
                "source_file": "Jira_Export_ATLAS.xlsx",
                "sheet": "Issues",
                "operation": "group_count",
                "group_by": "Status",
                "filters": [
                    {
                        "field": "Status",
                        "operator": "in",
                        "value": ["To Do", "In Progress"],
                    }
                ],
            })

        query, params = execute.call_args.args

        self.assertIn("IN (%s, %s)", query)

        self.assertEqual(
            params,
            (
                "Status",
                "Jira_Export_ATLAS.xlsx",
                "Issues:%",
                "Status",
                "To Do",
                "In Progress",
            ),
        )

    def test_structured_search_detects_truncated_results(self):
        rows = [
            {"id": str(index)}
            for index in range(4)
        ]

        with patch(
            "app.agent.sql_tool._execute_query",
            return_value=rows,
        ):
            result = execute_structured_query({
                "source_file": "Employee_Master.xlsx",
                "sheet": "Employees",
                "operation": "search",
                "limit": 3,
            })

        self.assertEqual(result["result_count"], 3)
        self.assertEqual(len(result["results"]), 3)
        self.assertTrue(result["truncated"])

    def test_empty_filter_list_is_allowed(self):
        with patch(
            "app.agent.sql_tool._execute_query",
            return_value=[{"total_count": 19}],
        ) as execute:

            result = execute_structured_query({
                "source_file": "Employee_Master.xlsx",
                "sheet": "Employees",
                "operation": "count",
                "filters": [],
            })

        self.assertEqual(
            result["results"],
            [{"total_count": 19}],
        )

        query, params = execute.call_args.args

        self.assertIn("COUNT(*)", query)

        self.assertEqual(
            params,
            (
                "Employee_Master.xlsx",
                "Employees:%",
            ),
        )


if __name__ == "__main__":
    unittest.main()
