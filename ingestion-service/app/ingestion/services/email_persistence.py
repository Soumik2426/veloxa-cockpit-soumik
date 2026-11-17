from uuid import UUID

from app.database.session import SessionLocal
from app.discovery.file_discovery import FileDiscoveryService
from app.ingestion.extractors.email_extractor import EmailExtractor
from app.ingestion.models import ExtractedRecord, IngestionFile


class EmailPersistenceService:

    def __init__(self):
        self.discovery_service = FileDiscoveryService()
        self.email_extractor = EmailExtractor()

    def persist_records(self, job_id: UUID):

        db = SessionLocal()

        try:
            email_files = (
                db.query(IngestionFile)
                .filter(
                    IngestionFile.ingestion_job_id == job_id,
                    IngestionFile.file_type == "EMAIL"
                )
                .all()
            )

            inserted_count = 0
            updated_count = 0

            for ingestion_file in email_files:

                file_path = (
                    self.discovery_service.input_directory
                    / ingestion_file.relative_path
                )

                if not file_path.exists():
                    raise FileNotFoundError(
                        f"Source email not found: {file_path}"
                    )

                email_data = self.email_extractor.extract(file_path)

                record_key = "EMAIL:1"

                source_locator = {
                    "file_name": ingestion_file.file_name,
                    "relative_path": ingestion_file.relative_path
                }

                existing_record = (
                    db.query(ExtractedRecord)
                    .filter(
                        ExtractedRecord.ingestion_file_id == ingestion_file.id,
                        ExtractedRecord.record_type == "EMAIL",
                        ExtractedRecord.record_key == record_key
                    )
                    .first()
                )

                if existing_record:

                    existing_record.source_locator = source_locator
                    existing_record.extracted_data = email_data
                    existing_record.extraction_method = "PYTHON_EMAIL"
                    existing_record.extraction_status = "SUCCESS"

                    updated_count += 1

                else:

                    db.add(
                        ExtractedRecord(
                            ingestion_file_id=ingestion_file.id,
                            record_type="EMAIL",
                            record_key=record_key,
                            source_locator=source_locator,
                            extracted_data=email_data,
                            extraction_method="PYTHON_EMAIL",
                            extraction_status="SUCCESS"
                        )
                    )

                    inserted_count += 1

            db.commit()

            return {
                "email_files": len(email_files),
                "inserted": inserted_count,
                "updated": updated_count
            }

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()
