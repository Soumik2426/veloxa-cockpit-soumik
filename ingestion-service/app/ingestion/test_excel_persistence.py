
from uuid import UUID

from app.ingestion.services.excel_persistence import (
    ExcelPersistenceService
)


if __name__ == "__main__":

    job_id = UUID(
        "12ec60f7-7e01-4947-a2fb-e9b202253e3e"
    )

    persistence_service = ExcelPersistenceService()

    result = persistence_service.persist_records(
        job_id=job_id
    )

    print("\nExcel persistence completed!")
    print(f"Excel files processed: {result['excel_files']}")
    print(f"Records inserted: {result['inserted']}")
    print(f"Records updated: {result['updated']}")
    print(f"Placeholder records: {result['placeholders']}")
