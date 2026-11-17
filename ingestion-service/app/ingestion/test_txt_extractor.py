from app.discovery.file_discovery import FileDiscoveryService
from app.ingestion.extractors.txt_extractor import TXTExtractor


if __name__ == "__main__":

    discovery_service = FileDiscoveryService()
    txt_extractor = TXTExtractor()

    files = [
        path
        for path in discovery_service.discover_files()
        if path.suffix.lower() == ".txt"
    ]

    successful = 0
    failed = 0

    for file_path in files:

        try:
            result = txt_extractor.extract(file_path)

            successful += 1

            print(f"\nFile: {file_path.name}")
            print(f"Characters: {result['character_count']}")
            print(f"Status: {result['record_status']}")
            print(f"\nContent preview:\n{result['text'][:500]}")

        except Exception as error:

            failed += 1

            print(f"\nFailed: {file_path.name}")
            print(f"Reason: {error}")

    print("\n========== TXT EXTRACTION SUMMARY ==========")
    print(f"Total TXT files: {len(files)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
