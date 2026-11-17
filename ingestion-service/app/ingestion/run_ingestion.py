from app.ingestion.create_ingestion_job import create_ingestion_job

from app.ingestion.services.file_registration import FileRegistrationService
from app.ingestion.services.file_classifier import FileClassificationService

from app.ingestion.services.csv_persistence import CSVPersistenceService
from app.ingestion.services.excel_persistence import ExcelPersistenceService
from app.ingestion.services.pdf_persistence import PDFPersistenceService
from app.ingestion.services.word_persistence import WordPersistenceService
from app.ingestion.services.email_persistence import EmailPersistenceService
from app.ingestion.services.txt_persistence import TXTPersistenceService

from app.ingestion.services.pdf_markdown_converter import PDFMarkdownConverter
from app.ingestion.services.word_markdown_converter import WordMarkdownConverter
from app.ingestion.services.email_markdown_converter import EmailMarkdownConverter
from app.ingestion.services.txt_markdown_converter import TXTMarkdownConverter


def run_ingestion():
    print("\n========== VELOXA INGESTION STARTED ==========\n")

    # Step 1: Create an ingestion job
    source_id, job_id = create_ingestion_job()

    # Step 2: Discover and register files
    print("\n========== FILE DISCOVERY AND REGISTRATION ==========\n")

    registration_service = FileRegistrationService()
    registration_service.register_files(source_id, job_id)

    # Step 3: Classify registered files
    print("\n========== FILE CLASSIFICATION ==========\n")

    classification_service = FileClassificationService()
    classification_service.classify_files(job_id)

    # Step 4: Extract and persist records
    print("\n========== RECORD PERSISTENCE ==========\n")

    persistence_services = [
        ("CSV", CSVPersistenceService()),
        ("Excel", ExcelPersistenceService()),
        ("PDF", PDFPersistenceService()),
        ("Word", WordPersistenceService()),
        ("Email", EmailPersistenceService()),
        ("TXT", TXTPersistenceService())
    ]

    for name, service in persistence_services:
        print(f"\nProcessing {name} files...")
        service.persist_records(job_id)

    # Step 5: Convert unstructured files into Markdown
    print("\n========== MARKDOWN CONVERSION ==========\n")

    markdown_converters = [
        ("PDF", PDFMarkdownConverter()),
        ("Word", WordMarkdownConverter()),
        ("Email", EmailMarkdownConverter()),
        ("TXT", TXTMarkdownConverter())
    ]

    for name, converter in markdown_converters:
        print(f"\nConverting {name} files into Markdown...")
        converter.convert_job(job_id)

    # Step 6: Completion summary
    print("\n========== VELOXA INGESTION COMPLETED ==========\n")
    print(f"Source ID: {source_id}")
    print(f"Job ID: {job_id}")
    print("All ingestion stages executed successfully.")


if __name__ == "__main__":
    run_ingestion()
