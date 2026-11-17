import pymupdf
from pathlib import Path


class PDFExtractor:

    def extract(self, file_path: Path) -> list[dict]:

        extracted_pages = []

        # Open the PDF document
        with pymupdf.open(file_path) as document:

            # Extract text from each page
            for page_number, page in enumerate(document, start=1):

                text = page.get_text("text").strip()

                # Skip pages containing no extractable text
                if not text:
                    continue

                extracted_pages.append({
                    "page_number": page_number,
                    "text": text,
                    "record_status": "DATA"
                })

        return extracted_pages
