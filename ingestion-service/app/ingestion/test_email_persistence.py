from uuid import UUID

from app.ingestion.services.email_persistence import (
    EmailPersistenceService
)


if __name__ == "__main__":

    job_id = UUID("12ec60f7-7e01-4947-a2fb-e9b202253e3e")

    service = EmailPersistenceService()
    result = service.persist_records(job_id)

    print("\nEmail persistence completed!")
    print(f"Email files: {result['email_files']}")
    print(f"Inserted records: {result['inserted']}")
    print(f"Updated records: {result['updated']}")
