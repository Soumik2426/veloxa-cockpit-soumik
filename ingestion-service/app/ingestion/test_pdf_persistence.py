from uuid import UUID

from app.ingestion.services.pdf_persistence import (
    PDFPersistenceService
)


if __name__ == "__main__":

    job_id = UUID(
        "12ec60f7-7e01-4947-a2fb-e9b202253e3e"
    )

    persistence_service = PDFPersistenceService()

    result = persistence_service.persist_records(
        job_id=job_id
    )

    print("\nPDF persistence completed!")
    print(f"PDF files processed: {result['pdf_files']}")
    print(f"Records inserted: {result['inserted']}")
    print(f"Records updated: {result['updated']}")
