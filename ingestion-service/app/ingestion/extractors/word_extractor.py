from pathlib import Path
from docx import Document


class WordExtractor:

    def extract(self, file_path: Path) -> list[dict]:

        document = Document(file_path)
        extracted_blocks = []

        # Extract paragraphs
        for index, paragraph in enumerate(document.paragraphs, start=1):

            text = paragraph.text.strip()

            if not text:
                continue

            extracted_blocks.append({
                "block_type": "PARAGRAPH",
                "block_number": index,
                "style": paragraph.style.name,
                "text": text,
                "record_status": "DATA"
            })

        # Extract tables
        for table_index, table in enumerate(document.tables, start=1):

            rows = []

            for row in table.rows:
                rows.append([
                    cell.text.strip()
                    for cell in row.cells
                ])

            if not rows:
                continue

            extracted_blocks.append({
                "block_type": "TABLE",
                "block_number": table_index,
                "rows": rows,
                "record_status": "DATA"
            })

        return extracted_blocks
