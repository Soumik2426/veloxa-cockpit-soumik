from uuid import UUID

from app.ingestion.services.txt_persistence import TXTPersistenceService


if __name__ == "__main__":

    job_id = UUID("12ec60f7-7e01-4947-a2fb-e9b202253e3e")

    service = TXTPersistenceService()
    result = service.persist_records(job_id)

    print("\nTXT persistence completed!")
    print(f"TXT files: {result['txt_files']}")
    print(f"Inserted records: {result['inserted']}")
    print(f"Updated records: {result['updated']}")
