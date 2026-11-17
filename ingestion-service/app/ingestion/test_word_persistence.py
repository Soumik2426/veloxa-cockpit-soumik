from uuid import UUID

from app.ingestion.services.word_persistence import WordPersistenceService


if __name__ == "__main__":

    job_id = UUID("12ec60f7-7e01-4947-a2fb-e9b202253e3e")

    service = WordPersistenceService()
    result = service.persist_records(job_id)

    print("\nWord persistence completed!")
    print(f"Word files: {result['word_files']}")
    print(f"Inserted records: {result['inserted']}")
    print(f"Updated records: {result['updated']}")
