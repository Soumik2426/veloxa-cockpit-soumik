from app.discovery.file_discovery import FileDiscoveryService
from app.ingestion.extractors.word_extractor import WordExtractor


if __name__ == "__main__":

    discovery_service = FileDiscoveryService()
    word_extractor = WordExtractor()

    files = [
        path
        for path in discovery_service.discover_files()
        if path.suffix.lower() == ".docx"
    ]

    successful = 0
    failed = 0
    total_blocks = 0

    for file_path in files:

        try:
            blocks = word_extractor.extract(file_path)

            successful += 1
            total_blocks += len(blocks)

            print(f"\nFile: {file_path.name}")
            print(f"Extracted blocks: {len(blocks)}")

            for block in blocks[:3]:
                print(f"  Type: {block['block_type']}")

                if block["block_type"] == "PARAGRAPH":
                    print(f"  Text: {block['text'][:150]}")

                elif block["block_type"] == "TABLE":
                    print(f"  Rows: {len(block['rows'])}")

        except Exception as error:
            failed += 1
            print(f"\nFailed: {file_path.name}")
            print(f"Reason: {error}")

    print("\n========== WORD EXTRACTION SUMMARY ==========")
    print(f"Total DOCX files: {len(files)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Total extracted blocks: {total_blocks}")
