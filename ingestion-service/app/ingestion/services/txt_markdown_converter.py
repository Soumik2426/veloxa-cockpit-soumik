import json
from pathlib import Path
from uuid import UUID

from app.database.connection import BASE_DIR
from app.database.session import SessionLocal
from app.discovery.file_discovery import FileDiscoveryService
from app.ingestion.extractors.txt_extractor import TXTExtractor
from app.ingestion.models import IngestionFile


PROJECT_ROOT = BASE_DIR.parent

MARKDOWN_OUTPUT_DIR = (
    PROJECT_ROOT / "data" / "processed" / "markdown"
)


class TXTMarkdownConverter:

    def __init__(self):
        self.discovery_service = FileDiscoveryService()
        self.txt_extractor = TXTExtractor()

    def convert_job(self, job_id: UUID):

        db = SessionLocal()

        try:
            txt_files = (
                db.query(IngestionFile)
                .filter(
                    IngestionFile.ingestion_job_id == job_id,
                    IngestionFile.file_type == "TEXT"
                )
                .all()
            )

            converted_count = 0
            failed_count = 0

            for ingestion_file in txt_files:

                try:
                    input_path = (
                        self.discovery_service.input_directory
                        / ingestion_file.relative_path
                    )

                    if not input_path.exists():
                        raise FileNotFoundError(
                            f"Source TXT file not found: {input_path}"
                        )

                    # Read directly from the original TXT file
                    txt_data = self.txt_extractor.extract(input_path)

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
                        "document_type: TEXT",
                        "---",
                        "",
                        f"# {ingestion_file.file_name}",
                        "",
                        txt_data["text"],
                        ""
                    ]

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
                "txt_files": len(txt_files),
                "converted": converted_count,
                "failed": failed_count,
                "output_directory": str(MARKDOWN_OUTPUT_DIR)
            }

        finally:
            db.close()
