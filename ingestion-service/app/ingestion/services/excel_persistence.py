import math
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from app.database.session import SessionLocal
from app.discovery.file_discovery import FileDiscoveryService
from app.ingestion.extractors.excel_extractor import ExcelExtractor
from app.ingestion.models import ExtractedRecord, IngestionFile


class ExcelPersistenceService:

    def __init__(self):
        self.discovery_service = FileDiscoveryService()
        self.excel_extractor = ExcelExtractor()

    @staticmethod
    def make_json_safe(value):
        """Convert extracted values into JSON-compatible values."""

        if isinstance(value, dict):
            return {
                str(key): ExcelPersistenceService.make_json_safe(item)
                for key, item in value.items()
            }

        if isinstance(value, (list, tuple)):
            return [
                ExcelPersistenceService.make_json_safe(item)
                for item in value
            ]

        if isinstance(value, (datetime, date)):
            return value.isoformat()

        if isinstance(value, Decimal):
            return str(value)

        if isinstance(value, float) and not math.isfinite(value):
            return None

        if value is None or isinstance(value, (str, int, float, bool)):
            return value

        return str(value)

    def persist_records(self, job_id: UUID):

        db = SessionLocal()

        try:
            # Step 1: Fetch all Excel files belonging to this job
            excel_files = (
                db.query(IngestionFile)
                .filter(
                    IngestionFile.ingestion_job_id == job_id,
                    IngestionFile.file_type == "EXCEL"
                )
                .all()
            )

            inserted_count = 0
            updated_count = 0
            placeholder_count = 0

            # Step 2: Process each Excel file
            for ingestion_file in excel_files:

                file_path = (
                    self.discovery_service.input_directory
                    / ingestion_file.relative_path
                )

                if not file_path.exists():
                    raise FileNotFoundError(
                        f"Source file not found: {file_path}"
                    )

                extracted_sheets = self.excel_extractor.extract(
                    file_path
                )

                # Step 3: Process every sheet
                for sheet in extracted_sheets:

                    sheet_name = sheet["sheet_name"]
                    header_row = sheet["header_row"]

                    for record in sheet["records"]:

                        row_number = record["row_number"]
                        record_status = record["record_status"]

                        if record_status == "PLACEHOLDER":
                            placeholder_count += 1

                        # Stable identity for this Excel row
                        record_key = f"{sheet_name}:{row_number}"

                        extracted_data = self.make_json_safe({
                            "record_status": record_status,
                            "data": record["data"]
                        })

                        source_locator = {
                            "sheet_name": sheet_name,
                            "row_number": row_number,
                            "header_row": header_row
                        }

                        # Step 4: Check whether this record already exists
                        existing_record = (
                            db.query(ExtractedRecord)
                            .filter(
                                ExtractedRecord.ingestion_file_id
                                == ingestion_file.id,
                                ExtractedRecord.record_type
                                == "EXCEL_ROW",
                                ExtractedRecord.record_key
                                == record_key
                            )
                            .first()
                        )

                        if existing_record:

                            # Update instead of inserting a duplicate
                            existing_record.source_locator = source_locator
                            existing_record.extracted_data = extracted_data
                            existing_record.extraction_method = (
                                "PYTHON_CALAMINE"
                            )
                            existing_record.extraction_status = "SUCCESS"

                            updated_count += 1

                        else:

                            extracted_record = ExtractedRecord(
                                ingestion_file_id=ingestion_file.id,
                                record_type="EXCEL_ROW",
                                record_key=record_key,
                                source_locator=source_locator,
                                extracted_data=extracted_data,
                                extraction_method="PYTHON_CALAMINE",
                                extraction_status="SUCCESS"
                            )

                            db.add(extracted_record)
                            inserted_count += 1

            # Step 5: Commit all database changes
            db.commit()

            return {
                "excel_files": len(excel_files),
                "inserted": inserted_count,
                "updated": updated_count,
                "placeholders": placeholder_count
            }

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()
