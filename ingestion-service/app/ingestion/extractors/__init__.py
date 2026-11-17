from pathlib import Path
from openpyxl import load_workbook


class ExcelExtractor:

    def extract(self, file_path: Path):

        workbook = load_workbook(
            filename=file_path,
            read_only=True,
            data_only=True
        )

        extracted_data = []

        try:
            for worksheet in workbook.worksheets:

                for row_number, row in enumerate(
                    worksheet.iter_rows(values_only=True),
                    start=1
                ):

                    values = list(row)

                    # Skip completely empty rows
                    if not any(value is not None for value in values):
                        continue

                    extracted_data.append({
                        "sheet_name": worksheet.title,
                        "row_number": row_number,
                        "values": values
                    })

        finally:
            workbook.close()

        return extracted_data
