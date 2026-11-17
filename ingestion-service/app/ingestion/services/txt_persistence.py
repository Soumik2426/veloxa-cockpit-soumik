from uuid import UUID

from app.database.session import SessionLocal
from app.discovery.file_discovery import FileDiscoveryService
from app.ingestion.extractors.txt_extractor import TXTExtractor
from app.ingestion.models import ExtractedRecord, IngestionFile


class TXTPersistenceService:

    def __init__(self):
        self.discovery_service = FileDiscoveryService()
        self.txt_extractor = TXTExtractor()

    def persist_records(self, job_id: UUID):

        db = SessionLocal()

        try:
            txt_files = (
                db.query(IngestionFile)
                .filter(
                    IngestionFile.ingestion_job_id == job_id,
                    IngestionFile.file_type == "TEXT"
                )
                .all()
            )

            inserted_count = 0
            updated_count = 0

            for ingestion_file in txt_files:

                file_path = (
                    self.discovery_service.input_directory
                    / ingestion_file.relative_path
                )

                if not file_path.exists():
                    raise FileNotFoundError(
                        f"Source text file not found: {file_path}"
                    )

                txt_data = self.txt_extractor.extract(file_path)

                record_key = "TEXT:1"

                source_locator = {
                    "file_name": ingestion_file.file_name,
                    "relative_path": ingestion_file.relative_path
                }

                existing_record = (
                    db.query(ExtractedRecord)
                    .filter(
                        ExtractedRecord.ingestion_file_id == ingestion_file.id,
                        ExtractedRecord.record_type == "TEXT",
                        ExtractedRecord.record_key == record_key
                    )
                    .first()
                )

                if existing_record:

                    existing_record.source_locator = source_locator
                    existing_record.extracted_data = txt_data
                    existing_record.extraction_method = "PYTHON_TEXT"
                    existing_record.extraction_status = "SUCCESS"

                    updated_count += 1

                else:

                    db.add(
                        ExtractedRecord(
                            ingestion_file_id=ingestion_file.id,
                            record_type="TEXT",
                            record_key=record_key,
                            source_locator=source_locator,
                            extracted_data=txt_data,
                            extraction_method="PYTHON_TEXT",
                            extraction_status="SUCCESS"
                        )
                    )

                    inserted_count += 1

            db.commit()

            return {
                "txt_files": len(txt_files),
                "inserted": inserted_count,
                "updated": updated_count
            }

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()
