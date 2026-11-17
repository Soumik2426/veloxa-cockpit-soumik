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


class UnifiedIngestionPipeline:

    def __init__(self):

        self.registration_service = FileRegistrationService()
        self.classification_service = FileClassificationService()

        # Structured data processors
        self.structured_processors = {
            "CSV": CSVPersistenceService(),
            "EXCEL": ExcelPersistenceService()
        }

        # Document processors
        self.document_processors = {
            "PDF": PDFPersistenceService(),
            "WORD": WordPersistenceService(),
            "EMAIL": EmailPersistenceService(),
            "TEXT": TXTPersistenceService()
        }

        # Markdown converters for unstructured documents
        self.markdown_converters = {
            "PDF": PDFMarkdownConverter(),
            "WORD": WordMarkdownConverter(),
            "EMAIL": EmailMarkdownConverter(),
            "TEXT": TXTMarkdownConverter()
        }

    def run(self, source_id, job_id):

        print("\n========== UNIFIED INGESTION STARTED ==========\n")

        # Stage 1: Discover and register files
        print("\n========== FILE DISCOVERY AND REGISTRATION ==========\n")

        self.registration_service.register_files(
            source_id,
            job_id
        )

        # Stage 2: Classify files
        print("\n========== FILE CLASSIFICATION ==========\n")

        self.classification_service.classify_files(job_id)

        # Stage 3: Process structured data
        print("\n========== STRUCTURED DATA PROCESSING ==========\n")

        for file_type, processor in self.structured_processors.items():

            print(f"\nProcessing {file_type} files...")

            result = processor.persist_records(job_id)

            print(f"{file_type} result: {result}")

        # Stage 4: Process unstructured documents
        print("\n========== DOCUMENT PROCESSING ==========\n")

        for file_type, processor in self.document_processors.items():

            print(f"\nProcessing {file_type} files...")

            result = processor.persist_records(job_id)

            print(f"{file_type} result: {result}")

        # Stage 5: Convert documents into Markdown
        print("\n========== MARKDOWN GENERATION ==========\n")

        for file_type, converter in self.markdown_converters.items():

            print(f"\nConverting {file_type} files...")

            result = converter.convert_job(job_id)

            print(f"{file_type} Markdown result: {result}")

        print("\n========== INGESTION COMPLETED ==========\n")

        print(f"Source ID: {source_id}")
        print(f"Job ID: {job_id}")

        return {
            "source_id": str(source_id),
            "job_id": str(job_id),
            "status": "COMPLETED"
        }
