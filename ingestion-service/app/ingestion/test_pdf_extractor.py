from app.discovery.file_discovery import FileDiscoveryService
from app.ingestion.extractors.pdf_extractor import PDFExtractor


if __name__ == "__main__":

    discovery_service = FileDiscoveryService()
    pdf_extractor = PDFExtractor()

    files = discovery_service.discover_files()

    pdf_files = [
        file_path
        for file_path in files
        if file_path.suffix.lower() == ".pdf"
    ]

    total_pages = 0
    successful_files = 0
    failed_files = 0

    for file_path in pdf_files:

        print("\n" + "=" * 80)
        print(f"FILE: {file_path.name}")
        print("=" * 80)

        try:
            extracted_pages = pdf_extractor.extract(file_path)

            successful_files += 1

            for page in extracted_pages:

                print(f"\nPage: {page['page_number']}")
                print(f"Status: {page['record_status']}")
                print("-" * 60)

                # Display only the first 500 characters
                print(page["text"][:500])

                total_pages += 1

        except Exception as error:

            failed_files += 1

            print(f"Extraction failed: {error}")

    print("\n" + "=" * 80)
    print("PDF EXTRACTION SUMMARY")
    print("=" * 80)

    print(f"PDF files discovered: {len(pdf_files)}")
    print(f"Successful files: {successful_files}")
    print(f"Failed files: {failed_files}")
    print(f"Pages containing extractable text: {total_pages}")
