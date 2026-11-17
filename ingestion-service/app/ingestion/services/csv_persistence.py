from uuid import UUID

from app.database.session import SessionLocal
from app.discovery.file_discovery import FileDiscoveryService
from app.ingestion.extractors.csv_extractor import CSVExtractor
from app.ingestion.models import ExtractedRecord, IngestionFile


class CSVPersistenceService:

    def __init__(self):
        self.discovery_service = FileDiscoveryService()
        self.csv_extractor = CSVExtractor()

    def persist_records(self, job_id: UUID):

        db = SessionLocal()

        try:
            csv_files = (
                db.query(IngestionFile)
                .filter(
                    IngestionFile.ingestion_job_id == job_id,
                    IngestionFile.file_type == "CSV"
                )
                .all()
            )

            inserted_count = 0
            updated_count = 0
            data_count = 0
            rejected_count = 0

            for ingestion_file in csv_files:

                file_path = (
                    self.discovery_service.input_directory
                    / ingestion_file.relative_path
                )

                if not file_path.exists():
                    raise FileNotFoundError(
                        f"Source CSV not found: {file_path}"
                    )

                extracted_rows = self.csv_extractor.extract(file_path)

                for row in extracted_rows:

                    row_number = row["row_number"]
                    record_key = f"ROW:{row_number}"

                    source_locator = {
                        "row_number": row_number
                    }

                    extracted_data = {
                        key: value
                        for key, value in row.items()
                        if key != "row_number"
                    }

                    if row["record_status"] == "DATA":
                        data_count += 1
                    else:
                        rejected_count += 1

                    existing_record = (
                        db.query(ExtractedRecord)
                        .filter(
                            ExtractedRecord.ingestion_file_id == ingestion_file.id,
                            ExtractedRecord.record_type == "CSV_ROW",
                            ExtractedRecord.record_key == record_key
                        )
                        .first()
                    )

                    if existing_record:

                        existing_record.source_locator = source_locator
                        existing_record.extracted_data = extracted_data
                        existing_record.extraction_method = "PYTHON_CSV"
                        existing_record.extraction_status = (
                            "SUCCESS"
                            if row["record_status"] == "DATA"
                            else "REJECTED"
                        )

                        updated_count += 1

                    else:

                        db.add(
                            ExtractedRecord(
                                ingestion_file_id=ingestion_file.id,
                                record_type="CSV_ROW",
                                record_key=record_key,
                                source_locator=source_locator,
                                extracted_data=extracted_data,
                                extraction_method="PYTHON_CSV",
                                extraction_status=(
                                    "SUCCESS"
                                    if row["record_status"] == "DATA"
                                    else "REJECTED"
                                )
                            )
                        )

                        inserted_count += 1

            db.commit()

            return {
                "csv_files": len(csv_files),
                "inserted": inserted_count,
                "updated": updated_count,
                "data_records": data_count,
                "rejected_records": rejected_count
            }

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()
