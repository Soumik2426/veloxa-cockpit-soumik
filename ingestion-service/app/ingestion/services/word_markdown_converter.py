import json
from pathlib import Path
from uuid import UUID

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

from app.database.connection import BASE_DIR
from app.database.session import SessionLocal
from app.discovery.file_discovery import FileDiscoveryService
from app.ingestion.models import IngestionFile


PROJECT_ROOT = BASE_DIR.parent

MARKDOWN_OUTPUT_DIR = (
    PROJECT_ROOT / "data" / "processed" / "markdown"
)


class WordMarkdownConverter:

    def __init__(self):
        self.discovery_service = FileDiscoveryService()

    @staticmethod
    def _escape_cell(value: str) -> str:
        return (
            value.replace("|", "\\|")
            .replace("\n", " ")
            .replace("\r", " ")
        )

    def _convert_paragraph(self, paragraph: Paragraph) -> str:

        text = paragraph.text.strip()

        if not text:
            return ""

        style = paragraph.style.name

        # Preserve Word heading hierarchy
        if style.startswith("Heading "):
            try:
                level = int(style.split()[-1])
                level = max(1, min(level, 6))
                return f"{'#' * level} {text}"
            except ValueError:
                pass

        if style == "Title":
            return f"# {text}"

        if style == "Subtitle":
            return f"### {text}"

        return text

    def _convert_table(self, table: Table) -> str:

        rows = [
            [
                self._escape_cell(cell.text.strip())
                for cell in row.cells
            ]
            for row in table.rows
        ]

        if not rows:
            return ""

        column_count = max(len(row) for row in rows)

        # Normalize rows to the same number of columns
        rows = [
            row + [""] * (column_count - len(row))
            for row in rows
        ]

        header = rows[0]

        separator = ["---"] * column_count

        markdown_rows = [
            "| " + " | ".join(header) + " |",
            "| " + " | ".join(separator) + " |"
        ]

        for row in rows[1:]:
            markdown_rows.append(
                "| " + " | ".join(row) + " |"
            )

        return "\n".join(markdown_rows)

    def convert_job(self, job_id: UUID):

        db = SessionLocal()

        try:
            word_files = (
                db.query(IngestionFile)
                .filter(
                    IngestionFile.ingestion_job_id == job_id,
                    IngestionFile.file_type == "WORD"
                )
                .all()
            )

            converted_count = 0
            failed_count = 0

            for ingestion_file in word_files:

                try:
                    input_path = (
                        self.discovery_service.input_directory
                        / ingestion_file.relative_path
                    )

                    if not input_path.exists():
                        raise FileNotFoundError(
                            f"Source Word document not found: {input_path}"
                        )

                    # Read directly from the original DOCX file
                    document = Document(input_path)

                    output_relative_path = (
                        Path(ingestion_file.relative_path)
                        .with_suffix(".md")
                    )

                    output_path = (
                        MARKDOWN_OUTPUT_DIR / output_relative_path
                    )

                    output_path.parent.mkdir(
                        parents=True,
                        exist_ok=True
                    )

                    markdown_parts = [
                        "---",
                        f"source_file_id: {ingestion_file.id}",
                        f"source_file: {json.dumps(ingestion_file.file_name)}",
                        f"source_path: {json.dumps(ingestion_file.relative_path)}",
                        f"checksum: {ingestion_file.checksum}",
                        "document_type: WORD",
                        "---",
                        "",
                        f"# {ingestion_file.file_name}",
                        ""
                    ]

                    # Iterate through paragraphs and tables
                    # in their original document order
                    for block in document.iter_inner_content():

                        if isinstance(block, Paragraph):
                            content = self._convert_paragraph(block)

                        elif isinstance(block, Table):
                            content = self._convert_table(block)

                        else:
                            continue

                        if content:
                            markdown_parts.extend([
                                content,
                                ""
                            ])

                    markdown_content = "\n".join(markdown_parts)

                    output_path.write_text(
                        markdown_content,
                        encoding="utf-8"
                    )

                    converted_count += 1

                    print(
                        f"Converted: {ingestion_file.relative_path}"
                    )

                except Exception as error:
                    failed_count += 1

                    print(
                        f"Failed: {ingestion_file.relative_path}"
                    )
                    print(f"Reason: {error}")

            return {
                "word_files": len(word_files),
                "converted": converted_count,
                "failed": failed_count,
                "output_directory": str(MARKDOWN_OUTPUT_DIR)
            }

        finally:
            db.close()
