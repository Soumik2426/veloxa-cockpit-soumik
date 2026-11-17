from uuid import UUID

from app.ingestion.services.txt_markdown_converter import (
    TXTMarkdownConverter
)


if __name__ == "__main__":

    job_id = UUID("12ec60f7-7e01-4947-a2fb-e9b202253e3e")

    converter = TXTMarkdownConverter()
    result = converter.convert_job(job_id)

    print("\nTXT Markdown conversion completed!")
    print(f"TXT files: {result['txt_files']}")
    print(f"Converted: {result['converted']}")
    print(f"Failed: {result['failed']}")
    print(f"Output directory: {result['output_directory']}")
