from uuid import UUID

from app.ingestion.services.word_markdown_converter import (
    WordMarkdownConverter
)


if __name__ == "__main__":

    job_id = UUID("12ec60f7-7e01-4947-a2fb-e9b202253e3e")

    converter = WordMarkdownConverter()
    result = converter.convert_job(job_id)

    print("\nWord Markdown conversion completed!")
    print(f"Word files: {result['word_files']}")
    print(f"Converted: {result['converted']}")
    print(f"Failed: {result['failed']}")
    print(f"Output directory: {result['output_directory']}")
