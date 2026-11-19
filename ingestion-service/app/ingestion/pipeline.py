import os
import logging
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import requests
from dotenv import load_dotenv

from app.database.session import SessionLocal
from app.ingestion.models import IngestionFile
from app.ingestion.services.csv_persistence import CSVPersistenceService
from app.ingestion.services.excel_persistence import ExcelPersistenceService
from app.ingestion.services.file_classifier import FileClassificationService
from app.ingestion.services.file_registration import FileRegistrationService


logger = logging.getLogger(__name__)

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

UNSTRUCTURED_TYPES = {"PDF", "WORD", "TEXT", "EMAIL"}


class UnifiedIngestionPipeline:
    """Route structured files locally and documents to the AI service."""

    def __init__(self):
        self.registration_service = FileRegistrationService()
        self.classification_service = FileClassificationService()

        self.structured_processors = {
            "CSV": CSVPersistenceService(),
            "EXCEL": ExcelPersistenceService(),
        }

        self.ai_service_url = os.getenv(
            "AI_SERVICE_URL",
            "http://localhost:8000",
        ).rstrip("/")

    @staticmethod
    def _update_document_statuses(documents, results):
        """
        Update individual ingestion_file records using AI service results.

        Successful statuses:
        - processed
        - skipped_unchanged

        Failure status:
        - failed
        """

        result_by_id = {
            str(item.get("file_id")): item
            for item in results
            if item.get("file_id")
        }

        db = SessionLocal()

        try:
            document_ids = [
                UUID(str(item["file_id"]))
                for item in documents
            ]

            records = (
                db.query(IngestionFile)
                .filter(IngestionFile.id.in_(document_ids))
                .all()
            )

            now = datetime.now(timezone.utc)

            for record in records:
                result = result_by_id.get(str(record.id))

                if result is None:
                    record.status = "FAILED"
                    continue

                result_status = str(
                    result.get("status", "")
                ).lower()

                if result_status in {"processed", "skipped_unchanged"}:
                    record.status = "PROCESSED"

                    # Preserve the original timestamp for unchanged files.
                    if (
                        result_status == "processed"
                        or record.processed_at is None
                    ):
                        record.processed_at = now

                else:
                    record.status = "FAILED"

            db.commit()

        except Exception:
            db.rollback()
            logger.exception(
                "Failed to update individual document ingestion statuses."
            )
            raise

        finally:
            db.close()

    def process_document_by_id(self, file_id):
        """
        Process exactly one existing unstructured document.

        Does not register, classify, or process other files.
        """

        file_uuid = UUID(str(file_id))

        db = SessionLocal()

        try:
            document = (
                db.query(IngestionFile)
                .filter(IngestionFile.id == file_uuid)
                .first()
            )

            if document is None:
                raise ValueError(
                    f"Ingestion file not found: {file_uuid}"
                )

            if document.file_type not in UNSTRUCTURED_TYPES:
                raise ValueError(
                    f"Unsupported document type: {document.file_type}"
                )

            payload_document = {
                "file_id": str(document.id),
                "file_name": document.file_name,
                "relative_path": document.relative_path,
                "file_type": document.file_type,
                "checksum": document.checksum,
                "job_id": str(document.ingestion_job_id),
            }

            payload = {
                "job_id": str(document.ingestion_job_id),
                "documents": [payload_document],
            }

            document.status = "PROCESSING"
            db.commit()

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()

        # ---------------------------------------------------------
        # Send only the selected document to the AI service
        # ---------------------------------------------------------

        try:
            response = requests.post(
                f"{self.ai_service_url}/api/v1/documents/process",
                json=payload,
                timeout=(10, 600),
            )

            response.raise_for_status()

            api_result = response.json()

            if (
                not isinstance(api_result, dict)
                or not isinstance(api_result.get("documents"), list)
            ):
                raise ValueError(
                    "AI service returned an invalid document response."
                )

            returned_results = api_result["documents"]

        except (requests.RequestException, ValueError) as error:
            logger.exception(
                "Single-document processing failed: %s",
                file_uuid,
            )

            returned_results = [
                {
                    "file_id": str(file_uuid),
                    "status": "failed",
                    "error": str(error),
                }
            ]

        # ---------------------------------------------------------
        # Ensure that the selected document has a result
        # ---------------------------------------------------------

        results_by_id = {
            str(item.get("file_id")): item
            for item in returned_results
            if isinstance(item, dict) and item.get("file_id")
        }

        results = [
            results_by_id.get(
                payload_document["file_id"],
                {
                    "file_id": payload_document["file_id"],
                    "status": "failed",
                    "error": "AI service did not return a result.",
                },
            )
        ]

        # ---------------------------------------------------------
        # Update the selected document's database status
        # ---------------------------------------------------------

        self._update_document_statuses(
            [payload_document],
            results,
        )

        result = results[0]

        result_status = str(
            result.get("status", "")
        ).lower()

        return {
            "file_id": str(file_uuid),
            "file_name": payload_document["file_name"],
            "status": (
                "COMPLETED"
                if result_status in {"processed", "skipped_unchanged"}
                else "FAILED"
            ),
            "document_result": result,
        }

    def run(self, source_id, job_id):
        self.registration_service.register_files(source_id, job_id)
        self.classification_service.classify_files(job_id)

        # ---------------------------------------------------------
        # Structured file processing
        # ---------------------------------------------------------

        structured_results = {}

        for file_type, processor in self.structured_processors.items():
            structured_results[file_type] = processor.persist_records(job_id)

        # ---------------------------------------------------------
        # Prepare unstructured document payload
        # ---------------------------------------------------------

        db = SessionLocal()

        try:
            documents = (
                db.query(IngestionFile)
                .filter(
                    IngestionFile.ingestion_job_id == job_id,
                    IngestionFile.file_type.in_(UNSTRUCTURED_TYPES),
                )
                .all()
            )

            payload = {
                "job_id": str(job_id),
                "documents": [
                    {
                        "file_id": str(item.id),
                        "file_name": item.file_name,
                        "relative_path": item.relative_path,
                        "file_type": item.file_type,
                        "checksum": item.checksum,
                        "job_id": str(job_id),
                    }
                    for item in documents
                ],
            }

            # Mark documents as processing before calling the AI service.
            for item in documents:
                item.status = "PROCESSING"

            if documents:
                db.commit()

        except Exception:
            db.rollback()
            logger.exception(
                "Failed to prepare unstructured documents for processing."
            )
            raise

        finally:
            db.close()

        submitted_documents = payload["documents"]

        # ---------------------------------------------------------
        # Default document processing response
        # ---------------------------------------------------------

        document_result = {
            "documents_received": len(submitted_documents),
            "successfully_processed": 0,
            "skipped_unchanged": 0,
            "chunks_generated": 0,
            "embeddings_generated": 0,
            "failed_documents": [],
            "documents": [],
        }

        # ---------------------------------------------------------
        # Send documents to AI service
        # ---------------------------------------------------------

        if submitted_documents:
            try:
                response = requests.post(
                    f"{self.ai_service_url}/api/v1/documents/process",
                    json=payload,
                    timeout=(10, 600),
                )

                response.raise_for_status()

                api_result = response.json()

                if not isinstance(api_result, dict):
                    raise ValueError(
                        "AI service returned an invalid response."
                    )

                document_result.update(api_result)

                # The API returns per-document outcomes in this list.
                results = document_result.get("documents", [])

                if not isinstance(results, list):
                    raise ValueError(
                        "AI service returned an invalid documents list."
                    )

            except (requests.RequestException, ValueError) as error:
                logger.exception(
                    "Unstructured document processing request failed."
                )

                # A request-level failure affects every submitted document.
                results = [
                    {
                        "file_id": item["file_id"],
                        "file_name": item["file_name"],
                        "relative_path": item["relative_path"],
                        "status": "failed",
                        "error": str(error),
                    }
                    for item in submitted_documents
                ]

                document_result = {
                    "documents_received": len(submitted_documents),
                    "successfully_processed": 0,
                    "skipped_unchanged": 0,
                    "chunks_generated": 0,
                    "embeddings_generated": 0,
                    "failed_documents": results,
                    "documents": results,
                }

            # -----------------------------------------------------
            # Update individual database statuses
            # -----------------------------------------------------

            self._update_document_statuses(
                submitted_documents,
                results,
            )

            # -----------------------------------------------------
            # Recalculate response counts from actual outcomes
            # -----------------------------------------------------

            successful_results = [
                item
                for item in results
                if str(item.get("status", "")).lower()
                in {"processed", "skipped_unchanged"}
            ]

            failed_results = [
                item
                for item in results
                if str(item.get("status", "")).lower()
                not in {"processed", "skipped_unchanged"}
            ]

            document_result["documents_received"] = len(
                submitted_documents
            )

            document_result["successfully_processed"] = len(
                successful_results
            )

            document_result["skipped_unchanged"] = sum(
                1
                for item in results
                if str(item.get("status", "")).lower()
                == "skipped_unchanged"
            )

            document_result["failed_documents"] = failed_results
            document_result["documents"] = results

        # ---------------------------------------------------------
        # Determine overall pipeline status
        # ---------------------------------------------------------

        failed_count = len(document_result["failed_documents"])
        total_documents = len(submitted_documents)

        if failed_count == 0:
            status = "COMPLETED"
        elif failed_count == total_documents:
            status = "FAILED"
        else:
            status = "PARTIAL_FAILURE"

        return {
            "source_id": str(source_id),
            "job_id": str(job_id),
            "status": status,
            "structured": structured_results,
            "documents": document_result,
        }
