from pathlib import Path
from python_calamine import CalamineWorkbook


class ExcelExtractor:

    @staticmethod
    def is_empty(value):
        return value is None or (
            isinstance(value, str) and not value.strip()
        )

    @classmethod
    def classify_record(cls, headers, row_data):

        non_empty_values = {
            key: value
            for key, value in row_data.items()
            if not cls.is_empty(value)
        }

        # Completely empty row
        if not non_empty_values:
            return "EMPTY"

        # Check whether the row contains only an identifier/reference
        identifier_headers = {
            "ref",
            "emp id",
            "id",
            "key",
            "req id"
        }

        meaningful_values = {
            key: value
            for key, value in non_empty_values.items()
            if key.strip().lower() not in identifier_headers
        }

        if not meaningful_values:
            return "PLACEHOLDER"

        return "DATA"

    def extract(self, file_path: Path):

        workbook = CalamineWorkbook.from_path(str(file_path))

        extracted_sheets = []

        for sheet_name in workbook.sheet_names:

            worksheet = workbook.get_sheet_by_name(sheet_name)
            rows = worksheet.to_python()

            # Step 1: Detect header row
            header_index = None

            for index, row in enumerate(rows):

                non_empty_values = [
                    value for value in row
                    if not self.is_empty(value)
                ]

                if len(non_empty_values) >= 2:
                    header_index = index
                    break

            if header_index is None:

                extracted_sheets.append({
                    "sheet_name": sheet_name,
                    "header_row": None,
                    "headers": [],
                    "records": []
                })

                continue

            # Step 2: Extract headers
            header_values = rows[header_index]

            headers = []

            for index, value in enumerate(header_values):

                if self.is_empty(value):
                    headers.append(f"column_{index + 1}")
                else:
                    headers.append(str(value).strip())

            records = []

            # Step 3: Extract records
            for row_index in range(header_index + 1, len(rows)):

                row = list(rows[row_index])

                if all(self.is_empty(value) for value in row):
                    continue

                # Match row length with header length
                row = row[:len(headers)]
                row.extend([None] * (len(headers) - len(row)))

                row_data = {
                    headers[index]: row[index]
                    for index in range(len(headers))
                }

                record_status = self.classify_record(
                    headers,
                    row_data
                )

                # Skip completely empty rows
                if record_status == "EMPTY":
                    continue

                records.append({
                    "row_number": row_index + 1,
                    "record_status": record_status,
                    "data": row_data
                })

            extracted_sheets.append({
                "sheet_name": sheet_name,
                "header_row": header_index + 1,
                "headers": headers,
                "records": records
            })

        return extracted_sheets
