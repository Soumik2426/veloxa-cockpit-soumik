
import os
import logging
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import requests
from dotenv import load_dotenv

from app.database.session import SessionLocal
from app.ingestion.models import IngestionFile, IngestionJob
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
        """Update individual document statuses using AI service results."""

        result_by_id = {
            str(item.get("file_id")): item
            for item in results
            if isinstance(item, dict) and item.get("file_id")
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

    def _update_job_status(self, job_id):
        """Recalculate job counts and final status from file statuses."""

        db = SessionLocal()

        try:
            job = (
                db.query(IngestionJob)
                .filter(IngestionJob.id == job_id)
                .first()
            )

            if job is None:
                raise ValueError("Ingestion job not found.")

            all_files = (
                db.query(IngestionFile)
                .filter(IngestionFile.ingestion_job_id == job_id)
                .all()
            )

            processed_count = sum(
                1 for item in all_files
                if item.status == "PROCESSED"
            )

            failed_count = sum(
                1 for item in all_files
                if item.status == "FAILED"
            )

            total_count = len(all_files)

            job.discovered_count = total_count
            job.processed_count = processed_count
            job.failed_count = failed_count
            job.completed_at = datetime.now(timezone.utc)

            if total_count > 0 and processed_count == total_count:
                job.status = "COMPLETED"
            elif processed_count == 0 and failed_count == total_count:
                job.status = "FAILED"
            else:
                job.status = "PARTIAL_FAILURE"

            db.commit()

            return {
                "discovered_count": total_count,
                "processed_count": processed_count,
                "failed_count": failed_count,
                "status": job.status,
            }

        except Exception:
            db.rollback()
            logger.exception(
                "Failed to update ingestion job status: %s",
                job_id,
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

        self._update_document_statuses(
            [payload_document],
            results,
        )

        result = results[0]
        result_status = str(result.get("status", "")).lower()

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
        """Run structured and unstructured ingestion for a job."""

        # ---------------------------------------------------------
        # Register and classify files
        # ---------------------------------------------------------

        self.registration_service.register_files(source_id, job_id)
        self.classification_service.classify_files(job_id)

        # ---------------------------------------------------------
        # Mark job as processing
        # ---------------------------------------------------------

        db = SessionLocal()

        try:
            job = (
                db.query(IngestionJob)
                .filter(IngestionJob.id == job_id)
                .first()
            )

            if job is None:
                raise ValueError("Ingestion job not found.")

            job.status = "PROCESSING"
            job.started_at = datetime.now(timezone.utc)
            job.completed_at = None
            job.processed_count = 0
            job.failed_count = 0
            job.error_message = None

            db.commit()

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()

        # ---------------------------------------------------------
        # Structured file processing
        # ---------------------------------------------------------

        structured_results = {}

        for file_type, processor in self.structured_processors.items():
            structured_results[file_type] = processor.persist_records(job_id)

        # Mark structured files processed after successful persistence.
        db = SessionLocal()

        try:
            structured_files = (
                db.query(IngestionFile)
                .filter(
                    IngestionFile.ingestion_job_id == job_id,
                    IngestionFile.file_type.in_(["CSV", "EXCEL"]),
                )
                .all()
            )

            now = datetime.now(timezone.utc)

            for record in structured_files:
                record.status = "PROCESSED"

                if record.processed_at is None:
                    record.processed_at = now

            db.commit()

        except Exception:
            db.rollback()
            logger.exception(
                "Failed to update structured file statuses."
            )
            raise

        finally:
            db.close()

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

            for item in documents:
                item.status = "PROCESSING"

            if documents:
                db.commit()

        except Exception:
            db.rollback()
            logger.exception(
                "Failed to prepare unstructured documents."
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

                results = document_result.get("documents", [])

                if not isinstance(results, list):
                    raise ValueError(
                        "AI service returned an invalid documents list."
                    )

            except (requests.RequestException, ValueError) as error:
                logger.exception(
                    "Unstructured document processing request failed."
                )

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
            # Update individual document statuses
            # -----------------------------------------------------

            self._update_document_statuses(
                submitted_documents,
                results,
            )

            # -----------------------------------------------------
            # Recalculate response counts
            # -----------------------------------------------------

            successful_results = [
                item for item in results
                if isinstance(item, dict)
                and str(item.get("status", "")).lower()
                in {"processed", "skipped_unchanged"}
            ]

            failed_results = [
                item for item in results
                if not isinstance(item, dict)
                or str(item.get("status", "")).lower()
                not in {"processed", "skipped_unchanged"}
            ]

            document_result["documents_received"] = len(
                submitted_documents
            )

            document_result["successfully_processed"] = len(
                successful_results
            )

            document_result["skipped_unchanged"] = sum(
                1 for item in successful_results
                if str(item.get("status", "")).lower()
                == "skipped_unchanged"
            )

            document_result["failed_documents"] = failed_results
            document_result["documents"] = results

        # ---------------------------------------------------------
        # Update final job status and counts
        # ---------------------------------------------------------

        job_summary = self._update_job_status(job_id)

        status = job_summary["status"]

        # ---------------------------------------------------------
        # Return pipeline result
        # ---------------------------------------------------------

        return {
            "source_id": str(source_id),
            "job_id": str(job_id),
            "status": status,
            "job_summary": job_summary,
            "structured": structured_results,
            "documents": document_result,
        }
