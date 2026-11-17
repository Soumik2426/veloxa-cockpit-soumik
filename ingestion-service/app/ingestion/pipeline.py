import os
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
            "AI_SERVICE_URL", "http://localhost:8000"
        ).rstrip("/")

    def run(self, source_id, job_id):
        self.registration_service.register_files(source_id, job_id)
        self.classification_service.classify_files(job_id)

        structured_results = {}
        for file_type, processor in self.structured_processors.items():
            structured_results[file_type] = processor.persist_records(job_id)

        db = SessionLocal()
        try:
            documents = db.query(IngestionFile).filter(
                IngestionFile.ingestion_job_id == job_id,
                IngestionFile.file_type.in_(UNSTRUCTURED_TYPES),
            ).all()
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
        finally:
            db.close()

        document_result = {
            "documents_received": 0,
            "successfully_processed": 0,
            "chunks_generated": 0,
            "embeddings_generated": 0,
            "failed_documents": [],
        }
        if payload["documents"]:
            try:
                response = requests.post(
                    f"{self.ai_service_url}/api/v1/documents/process",
                    json=payload,
                    timeout=(10, 600),
                )
                response.raise_for_status()
                document_result = response.json()
            except (requests.RequestException, ValueError) as error:
                document_result["failed_documents"] = [
                    {"job_id": str(job_id), "error": str(error)}
                ]
                document_result["documents_received"] = len(payload["documents"])

        failed = document_result.get("failed_documents", [])
        status = "COMPLETED" if not failed else "PARTIAL_FAILURE"
        if failed and len(failed) >= len(payload["documents"]):
            status = "FAILED"

        return {
            "source_id": str(source_id),
            "job_id": str(job_id),
            "status": status,
            "structured": structured_results,
            "documents": document_result,
        }
