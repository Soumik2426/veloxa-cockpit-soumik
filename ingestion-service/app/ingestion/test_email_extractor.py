from app.discovery.file_discovery import FileDiscoveryService
from app.ingestion.extractors.email_extractor import EmailExtractor


if __name__ == "__main__":

    discovery_service = FileDiscoveryService()
    email_extractor = EmailExtractor()

    files = [
        path
        for path in discovery_service.discover_files()
        if path.suffix.lower() == ".eml"
    ]

    successful = 0
    failed = 0

    for file_path in files:

        try:
            result = email_extractor.extract(file_path)

            successful += 1

            print(f"\nFile: {file_path.name}")
            print(f"Subject: {result['subject']}")
            print(f"Sender: {result['sender']}")
            print(f"Recipient: {result['recipient']}")
            print(f"Date: {result['date']}")
            print(f"Body preview: {result['body'][:200]}")
            print(f"Attachments: {len(result['attachments'])}")

        except Exception as error:

            failed += 1

            print(f"\nFailed: {file_path.name}")
            print(f"Reason: {error}")

    print("\n========== EMAIL EXTRACTION SUMMARY ==========")
    print(f"Total email files: {len(files)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
