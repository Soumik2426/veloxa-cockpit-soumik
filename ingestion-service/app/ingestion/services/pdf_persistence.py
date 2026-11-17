from uuid import UUID

from app.database.session import SessionLocal
from app.discovery.file_discovery import FileDiscoveryService
from app.ingestion.extractors.pdf_extractor import PDFExtractor
from app.ingestion.models import ExtractedRecord, IngestionFile


class PDFPersistenceService:

    def __init__(self):
        self.discovery_service = FileDiscoveryService()
        self.pdf_extractor = PDFExtractor()

    def persist_records(self, job_id: UUID):

        db = SessionLocal()

        try:
            # Step 1: Fetch registered PDF files for this job
            pdf_files = (
                db.query(IngestionFile)
                .filter(
                    IngestionFile.ingestion_job_id == job_id,
                    IngestionFile.file_type == "PDF"
                )
                .all()
            )

            inserted_count = 0
            updated_count = 0

            # Step 2: Process each PDF
            for ingestion_file in pdf_files:

                file_path = (
                    self.discovery_service.input_directory
                    / ingestion_file.relative_path
                )

                if not file_path.exists():
                    raise FileNotFoundError(
                        f"Source PDF not found: {file_path}"
                    )

                extracted_pages = self.pdf_extractor.extract(
                    file_path
                )

                # Step 3: Process each extracted page
                for page in extracted_pages:

                    page_number = page["page_number"]

                    record_key = f"PAGE:{page_number}"

                    source_locator = {
                        "page_number": page_number
                    }

                    extracted_data = {
                        "record_status": page["record_status"],
                        "text": page["text"]
                    }

                    # Step 4: Check whether this page already exists
                    existing_record = (
                        db.query(ExtractedRecord)
                        .filter(
                            ExtractedRecord.ingestion_file_id
                            == ingestion_file.id,
                            ExtractedRecord.record_type
                            == "PDF_PAGE",
                            ExtractedRecord.record_key
                            == record_key
                        )
                        .first()
                    )

                    if existing_record:

                        existing_record.source_locator = source_locator
                        existing_record.extracted_data = extracted_data
                        existing_record.extraction_method = "PYMUPDF"
                        existing_record.extraction_status = "SUCCESS"

                        updated_count += 1

                    else:

                        extracted_record = ExtractedRecord(
                            ingestion_file_id=ingestion_file.id,
                            record_type="PDF_PAGE",
                            record_key=record_key,
                            source_locator=source_locator,
                            extracted_data=extracted_data,
                            extraction_method="PYMUPDF",
                            extraction_status="SUCCESS"
                        )

                        db.add(extracted_record)
                        inserted_count += 1

            # Step 5: Commit database changes
            db.commit()

            return {
                "pdf_files": len(pdf_files),
                "inserted": inserted_count,
                "updated": updated_count
            }

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()
