from app.discovery.file_discovery import FileDiscoveryService
from app.ingestion.extractors.csv_extractor import CSVExtractor


if __name__ == "__main__":

    discovery_service = FileDiscoveryService()
    csv_extractor = CSVExtractor()

    files = [
        path
        for path in discovery_service.discover_files()
        if path.suffix.lower() == ".csv"
    ]

    successful = 0
    failed = 0
    total_data = 0
    total_rejected = 0

    for file_path in files:

        try:
            records = csv_extractor.extract(file_path)

            successful += 1

            data_records = [
                record for record in records
                if record["record_status"] == "DATA"
            ]

            rejected_records = [
                record for record in records
                if record["record_status"] == "REJECTED"
            ]

            total_data += len(data_records)
            total_rejected += len(rejected_records)

            print(f"\nFile: {file_path.name}")
            print(f"Data records: {len(data_records)}")
            print(f"Rejected records: {len(rejected_records)}")

            for record in records[:5]:
                print(record)

        except Exception as error:

            failed += 1

            print(f"\nFailed: {file_path.name}")
            print(f"Reason: {error}")

    print("\n========== CSV EXTRACTION SUMMARY ==========")
    print(f"Total CSV files: {len(files)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Total data records: {total_data}")
    print(f"Total rejected records: {total_rejected}")
