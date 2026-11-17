from uuid import UUID

from app.ingestion.services.csv_persistence import CSVPersistenceService


if __name__ == "__main__":

    job_id = UUID("12ec60f7-7e01-4947-a2fb-e9b202253e3e")

    service = CSVPersistenceService()
    result = service.persist_records(job_id)

    print("\nCSV persistence completed!")
    print(f"CSV files: {result['csv_files']}")
    print(f"Inserted records: {result['inserted']}")
    print(f"Updated records: {result['updated']}")
    print(f"Valid data records: {result['data_records']}")
    print(f"Rejected records: {result['rejected_records']}")
