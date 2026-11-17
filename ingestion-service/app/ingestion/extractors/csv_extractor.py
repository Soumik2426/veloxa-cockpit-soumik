import csv
from pathlib import Path


class CSVExtractor:

    def extract(self, file_path: Path) -> list[dict]:

        extracted_rows = []

        with open(
            file_path,
            mode="r",
            encoding="utf-8-sig",
            newline=""
        ) as csv_file:

            reader = csv.reader(csv_file)

            headers = None

            for row_number, row in enumerate(reader, start=1):

                # Skip completely empty rows
                if not row or all(not value.strip() for value in row):
                    continue

                # First non-empty row is treated as the header
                if headers is None:
                    headers = [
                        header.strip()
                        for header in row
                    ]
                    continue

                # Detect malformed rows
                if len(row) != len(headers):

                    extracted_rows.append({
                        "row_number": row_number,
                        "record_status": "REJECTED",
                        "error": (
                            f"Expected {len(headers)} columns, "
                            f"but received {len(row)}"
                        ),
                        "raw_data": row
                    })

                    continue

                # Preserve all values as strings
                row_data = {
                    headers[index]: row[index].strip()
                    for index in range(len(headers))
                }

                extracted_rows.append({
                    "row_number": row_number,
                    "record_status": "DATA",
                    "data": row_data
                })

        return extracted_rows
