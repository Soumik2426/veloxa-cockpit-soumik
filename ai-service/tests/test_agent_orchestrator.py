
import unittest
from uuid import uuid4
from unittest.mock import patch

from pydantic import ValidationError

from app.agent.orchestrator import (
    GeminiServiceError,
    answer_question,
)
from app.agent.schemas import AgentAskRequest, AnswerDraft, RetrievalPlan
from app.api import DocumentBatch, ask_agent, process_documents
from fastapi import HTTPException


def sql_row():
    return {
        "id": uuid4(),
        "record_type": "CSV_ROW",
        "record_key": "ROW:2",
        "source_locator": {"row_number": 2},
        "extracted_data": {"data": {"project": "Orion", "status": "delayed"}},
        "extraction_method": "PYTHON_CSV",
        "confidence_score": None,
        "created_at": "2026-01-01T00:00:00+00:00",
        "file_name": "projects.csv",
        "relative_path": "reports/projects.csv",
        "file_type": "CSV",
    }


def rag_chunk():
    return {
        "chunk_id": "chunk-1",
        "content": "The Orion team reported blocked delivery dependencies.",
        "source_file": "weekly-review.docx",
        "source_path": "reports/weekly-review.docx",
        "document_type": "WORD",
        "section": "Delivery risks",
        "similarity": 0.91,
    }


class AgentOrchestratorTests(unittest.TestCase):

    def setUp(self):
        self.catalogue_patcher = patch(
            "app.agent.orchestrator.discover_structured_catalogue",
            return_value={
                "Employee_Master.xlsx": {
                    "Employees": {
                        "fields": ["Emp ID", "Full Name", "Manager ID"],
                        "field_details": {},
                    }
                },
                "Jira_Export_ATLAS.xlsx": {
                    "Issues": {
                        "fields": ["Key", "Status", "Story Points"],
                        "field_details": {},
                    }
                },
            },
        )
        self.catalogue_patcher.start()

    def tearDown(self):
        self.catalogue_patcher.stop()

    def run_with_plan(self, plan, answer=None):
        generated = [plan]

        if answer is not None:
            generated.append(answer)

        return patch(
            "app.agent.orchestrator._generate_json",
            side_effect=generated,
        )

    def test_empty_planner_result_uses_generic_retrieval_fallback(self):
        from app.agent.orchestrator import _plan

        with patch(
            "app.agent.orchestrator._generate_json",
            return_value=RetrievalPlan(sources=[]),
        ):
            plan = _plan("Summarise the latest operational risks")

        self.assertEqual(plan.sources, ["sql", "rag"])
        self.assertTrue(plan.search_terms)
        self.assertEqual(
            plan.rag_query,
            "Summarise the latest operational risks",
        )

    def test_sql_only_question_uses_structured_records(self):
        plan = RetrievalPlan(
            sources=["sql"],
            search_terms=["revenue"],
        )

        answer = AnswerDraft(
            answer="The row shows a delay [SQL-1]."
        )

        with self.run_with_plan(plan, answer), \
             patch(
                 "app.agent.orchestrator.search_structured_records",
                 return_value=[sql_row()],
             ) as sql, \
             patch(
                 "app.agent.orchestrator.retrieve_relevant_chunks"
             ) as rag:

            response = answer_question(
                "What is the status of Orion?"
            )

        sql.assert_called_once_with(["revenue"])
        rag.assert_not_called()

        self.assertEqual(response.retrieval_sources, ["sql"])
        self.assertEqual(
            response.evidence[0]["source_reference"]["file_name"],
            "projects.csv",
        )
        self.assertEqual(response.confidence.level, "moderate")

    def test_rag_only_question_uses_existing_retriever(self):
        plan = RetrievalPlan(
            sources=["rag"],
            rag_query="delivery blockers",
        )

        answer = AnswerDraft(
            answer="The review reports blocked dependencies [RAG-1]."
        )

        with self.run_with_plan(plan, answer), \
             patch(
                 "app.agent.orchestrator.search_structured_records"
             ) as sql, \
             patch(
                 "app.agent.orchestrator.retrieve_relevant_chunks",
                 return_value=[rag_chunk()],
             ) as rag:

            response = answer_question(
                "Why is delivery blocked?"
            )

        sql.assert_not_called()
        rag.assert_called_once_with(
            "delivery blockers",
            top_k=10,
        )

        self.assertEqual(
            response.evidence[0]["evidence_id"],
            "RAG-1",
        )
        self.assertEqual(response.confidence.level, "moderate")

    def test_hybrid_question_combines_sql_and_document_evidence(self):
        plan = RetrievalPlan(
            sources=["sql", "rag"],
            search_terms=["Orion"],
            rag_query="Orion delivery",
        )

        answer = AnswerDraft(
            answer=(
                "The row shows a delay [SQL-1], "
                "and the review cites dependencies [RAG-1]."
            )
        )

        with self.run_with_plan(plan, answer), \
             patch(
                 "app.agent.orchestrator.search_structured_records",
                 return_value=[sql_row()],
             ), \
             patch(
                 "app.agent.orchestrator.retrieve_relevant_chunks",
                 return_value=[rag_chunk()],
             ):

            response = answer_question(
                "Compare Orion's delivery status with management commentary."
            )

        self.assertEqual(
            response.retrieval_sources,
            ["sql", "rag"],
        )

        self.assertEqual(
            [item["evidence_id"] for item in response.evidence],
            ["SQL-1", "RAG-1"],
        )

        self.assertEqual(response.confidence.level, "high")

    def test_no_evidence_returns_insufficient_answer_without_final_generation(self):
        plan = RetrievalPlan(
            sources=["sql", "rag"],
            search_terms=["unknown"],
        )

        with self.run_with_plan(plan), \
             patch(
                 "app.agent.orchestrator.search_structured_records",
                 return_value=[],
             ), \
             patch(
                 "app.agent.orchestrator.retrieve_relevant_chunks",
                 return_value=[],
             ):

            response = answer_question(
                "What happened to the unknown project?"
            )

        self.assertIn("cannot determine", response.answer)
        self.assertEqual(response.confidence.level, "low")
        self.assertEqual(response.evidence, [])
        self.assertEqual(len(response.limitations), 1)

    def test_conflicts_are_reported_and_lower_confidence(self):
        plan = RetrievalPlan(
            sources=["sql", "rag"],
            search_terms=["Orion"],
            rag_query="Orion",
        )

        answer = AnswerDraft(
            answer="Records disagree about the delivery date.",
            conflicts=[
                "The structured row says delayed while the review describes delivery as complete."
            ],
        )

        with self.run_with_plan(plan, answer), \
             patch(
                 "app.agent.orchestrator.search_structured_records",
                 return_value=[sql_row()],
             ), \
             patch(
                 "app.agent.orchestrator.retrieve_relevant_chunks",
                 return_value=[rag_chunk()],
             ):

            response = answer_question(
                "Was Orion delivered?"
            )

        self.assertEqual(response.confidence.level, "low")

        self.assertTrue(
            any(
                "Conflicting evidence" in item
                for item in response.limitations
            )
        )

    def test_database_failure_is_reported_without_fabricating_evidence(self):
        plan = RetrievalPlan(
            sources=["sql"],
            search_terms=["revenue"],
        )

        with self.run_with_plan(plan), \
             patch(
                 "app.agent.orchestrator.search_structured_records",
                 side_effect=OSError("db unavailable"),
             ):

            response = answer_question(
                "What was the revenue?"
            )

        self.assertEqual(response.confidence.level, "low")
        self.assertEqual(response.evidence, [])

        self.assertIn(
            "Structured record retrieval was unavailable.",
            response.limitations,
        )

    def test_gemini_failure_during_planning_is_safely_reported(self):
        with patch(
            "app.agent.orchestrator._generate_json",
            side_effect=GeminiServiceError("Gemini request failed."),
        ):
            with self.assertRaises(GeminiServiceError):
                answer_question("Summarize delivery risks.")

    def test_gemini_failure_during_answer_generation_is_safely_reported(self):
        plan = RetrievalPlan(
            sources=["sql"],
            search_terms=["Orion"],
        )

        with patch(
            "app.agent.orchestrator._generate_json",
            side_effect=[
                plan,
                GeminiServiceError("Gemini request failed."),
            ],
        ), patch(
            "app.agent.orchestrator.search_structured_records",
            return_value=[sql_row()],
        ):
            with self.assertRaises(GeminiServiceError):
                answer_question("What is happening with Orion?")

    def test_empty_question_is_rejected(self):
        with self.assertRaises(ValidationError):
            AgentAskRequest(question="")

        with self.assertRaises(ValueError):
            answer_question("   ")

    def test_agent_endpoint_maps_gemini_failure_to_gateway_error(self):
        with patch(
            "app.api.answer_question",
            side_effect=GeminiServiceError("private details"),
        ):
            with self.assertRaises(HTTPException) as raised:
                ask_agent(
                    AgentAskRequest(
                        question="Summarize delivery risks."
                    )
                )

        self.assertEqual(raised.exception.status_code, 502)
        self.assertNotIn(
            "private details",
            str(raised.exception.detail),
        )

    def test_document_processing_endpoint_contract_remains_available(self):
        job_id = uuid4()

        batch = DocumentBatch(
            job_id=job_id,
            documents=[
                {
                    "file_id": uuid4(),
                    "file_name": "memo.txt",
                    "relative_path": "memo.txt",
                    "file_type": "TEXT",
                    "checksum": "a" * 64,
                    "job_id": job_id,
                }
            ],
        )

        with patch(
            "app.api.process_document",
            return_value={
                "file_id": str(batch.documents[0].file_id),
                "status": "processed",
                "chunks": 2,
                "embeddings": 2,
            },
        ) as processor:

            response = process_documents(batch)

        processor.assert_called_once()

        self.assertEqual(response["documents_received"], 1)
        self.assertEqual(response["successfully_processed"], 1)
        self.assertEqual(response["chunks_generated"], 2)
        self.assertEqual(response["failed_documents"], [])


if __name__ == "__main__":
    unittest.main()


    def test_planner_normalizes_common_aggregation_aliases_and_null_limits(self):
        from app.agent.orchestrator import _normalize_retrieval_plan

        normalized = _normalize_retrieval_plan({
            "sources": ["sql"],
            "structured_queries": [{
                "source_file": "Jira_Export_ATLAS.xlsx",
                "sheet": "Issues",
                "operation": "group_sum",
                "numeric_field": "Story Points",
                "group_field": "Status",
                "limit": None,
                "filters": [],
            }],
        })

        query = normalized["structured_queries"][0]
        self.assertEqual(query["field"], "Story Points")
        self.assertEqual(query["group_by"], "Status")
        self.assertEqual(query["limit"], 25)

    def test_planner_drops_invalid_query_without_failing_whole_plan(self):
        from app.agent.orchestrator import _normalize_retrieval_plan

        normalized = _normalize_retrieval_plan({
            "sources": ["sql", "rag"],
            "rag_query": "incident details",
            "structured_queries": [{
                "source_file": "Incidents_Aug-Oct_2026.xlsx",
                "sheet": "Incidents",
                "operation": "group_count",
                "filters": [],
            }],
        })

        self.assertEqual(normalized["structured_queries"], [])
        self.assertEqual(normalized["sources"], ["sql", "rag"])
        plan = RetrievalPlan.model_validate(normalized)
        self.assertEqual(plan.sources, ["sql", "rag"])

    def test_between_filter_is_normalized_and_validated(self):
        from app.agent.orchestrator import _normalize_retrieval_plan

        normalized = _normalize_retrieval_plan({
            "sources": ["sql"],
            "structured_queries": [{
                "source_file": "GL_Export_Apr-Sep_2026.xlsx",
                "sheet": "GL Apr-Sep",
                "operation": "search",
                "filters": [{
                    "field": "Txn Date",
                    "operator": "between",
                    "value": ["2026-04-01", "2026-09-30"],
                }],
            }],
        })

        plan = RetrievalPlan.model_validate(normalized)
        self.assertEqual(plan.structured_queries[0].filters[0].operator, "between")

    def test_prompt_evidence_is_bounded(self):
        from app.agent.orchestrator import _compact_evidence_for_prompt

        evidence = [{
            "evidence_id": "RAG-1",
            "source": "rag",
            "source_reference": {"file_name": "long.docx"},
            "content": "x" * 12000,
        }]

        compact, truncated = _compact_evidence_for_prompt(evidence)
        self.assertTrue(truncated)
        self.assertLessEqual(len(str(compact)), 4000)
        self.assertEqual(compact[0]["evidence_id"], "RAG-1")
