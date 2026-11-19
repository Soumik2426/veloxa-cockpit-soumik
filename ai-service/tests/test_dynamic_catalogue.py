import unittest
from unittest.mock import patch
from app.agent.sql_tool import _validate_source, discover_structured_catalogue

class DynamicCatalogueTests(unittest.TestCase):
    @patch("app.agent.sql_tool._execute_query")
    def test_catalogue_groups_sources_sheets_and_fields(self, execute):
        execute.return_value = [
            {"file_name":"new.xlsx","sheet_name":"Overview","field_name":"Revenue","observed_types":"number","observed_records":4},
            {"file_name":"new.xlsx","sheet_name":"Overview","field_name":"Region","observed_types":"string","observed_records":4},
        ]
        result = discover_structured_catalogue()
        self.assertEqual(result["new.xlsx"]["Overview"]["fields"], ["Revenue","Region"])

    @patch("app.agent.sql_tool.discover_structured_catalogue")
    def test_validation_uses_discovered_schema(self, discover):
        discover.return_value = {"new.xlsx":{"Overview":{"fields":["Revenue","Region"]}}}
        self.assertEqual(_validate_source("new.xlsx","Overview"), {"Revenue","Region"})

    @patch("app.agent.sql_tool.discover_structured_catalogue", return_value={})
    def test_unknown_source_is_rejected(self, _discover):
        with self.assertRaises(ValueError):
            _validate_source("missing.xlsx","Sheet1")

if __name__ == "__main__":
    unittest.main()
