from collections import Counter

from app.discovery.file_discovery import FileDiscoveryService
from app.ingestion.extractors.excel_extractor import ExcelExtractor


if __name__ == "__main__":

    discovery_service = FileDiscoveryService()
    extractor = ExcelExtractor()

    all_files = discovery_service.discover_files()

    excel_files = [
        file_path
        for file_path in all_files
        if file_path.suffix.lower() == ".xlsx"
    ]

    total_data = 0
    total_placeholders = 0
    total_failed = 0

    for file_path in excel_files:

        print("\n" + "=" * 80)
        print(f"FILE: {file_path.name}")
        print("=" * 80)

        try:
            sheets = extractor.extract(file_path)

            file_counts = Counter()

            for sheet in sheets:

                print(f"\nSheet: {sheet['sheet_name']}")
                print(f"Header row: {sheet['header_row']}")

                for record in sheet["records"]:

                    status = record["record_status"]
                    file_counts[status] += 1

                    if status == "PLACEHOLDER":
                        print(
                            f"Placeholder at row "
                            f"{record['row_number']}: "
                            f"{record['data']}"
                        )

            print("\nFile summary:")
            print(f"DATA: {file_counts['DATA']}")
            print(f"PLACEHOLDER: {file_counts['PLACEHOLDER']}")

            total_data += file_counts["DATA"]
            total_placeholders += file_counts["PLACEHOLDER"]

        except Exception as error:
            total_failed += 1
            print(f"Extraction failed: {error}")

    print("\n" + "=" * 80)
    print("EXTRACTION CLASSIFICATION SUMMARY")
    print("=" * 80)
    print(f"Excel files: {len(excel_files)}")
    print(f"Successful files: {len(excel_files) - total_failed}")
    print(f"Failed files: {total_failed}")
    print(f"DATA records: {total_data}")
    print(f"PLACEHOLDER records: {total_placeholders}")
