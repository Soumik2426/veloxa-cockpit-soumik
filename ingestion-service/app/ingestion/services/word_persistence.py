from uuid import UUID

from app.database.session import SessionLocal
from app.discovery.file_discovery import FileDiscoveryService
from app.ingestion.extractors.word_extractor import WordExtractor
from app.ingestion.models import ExtractedRecord, IngestionFile


class WordPersistenceService:

    def __init__(self):
        self.discovery_service = FileDiscoveryService()
        self.word_extractor = WordExtractor()

    def persist_records(self, job_id: UUID):

        db = SessionLocal()

        try:
            word_files = (
                db.query(IngestionFile)
                .filter(
                    IngestionFile.ingestion_job_id == job_id,
                    IngestionFile.file_type == "WORD"
                )
                .all()
            )

            inserted_count = 0
            updated_count = 0

            for ingestion_file in word_files:

                file_path = (
                    self.discovery_service.input_directory
                    / ingestion_file.relative_path
                )

                if not file_path.exists():
                    raise FileNotFoundError(
                        f"Source Word document not found: {file_path}"
                    )

                extracted_blocks = self.word_extractor.extract(file_path)

                for block in extracted_blocks:

                    block_type = block["block_type"]
                    block_number = block["block_number"]

                    record_key = f"{block_type}:{block_number}"

                    source_locator = {
                        "block_type": block_type,
                        "block_number": block_number
                    }

                    extracted_data = {
                        key: value
                        for key, value in block.items()
                        if key not in ("block_type", "block_number")
                    }

                    existing_record = (
                        db.query(ExtractedRecord)
                        .filter(
                            ExtractedRecord.ingestion_file_id == ingestion_file.id,
                            ExtractedRecord.record_type == "WORD_BLOCK",
                            ExtractedRecord.record_key == record_key
                        )
                        .first()
                    )

                    if existing_record:

                        existing_record.source_locator = source_locator
                        existing_record.extracted_data = extracted_data
                        existing_record.extraction_method = "PYTHON_DOCX"
                        existing_record.extraction_status = "SUCCESS"

                        updated_count += 1

                    else:

                        db.add(
                            ExtractedRecord(
                                ingestion_file_id=ingestion_file.id,
                                record_type="WORD_BLOCK",
                                record_key=record_key,
                                source_locator=source_locator,
                                extracted_data=extracted_data,
                                extraction_method="PYTHON_DOCX",
                                extraction_status="SUCCESS"
                            )
                        )

                        inserted_count += 1

            db.commit()

            return {
                "word_files": len(word_files),
                "inserted": inserted_count,
                "updated": updated_count
            }

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()
