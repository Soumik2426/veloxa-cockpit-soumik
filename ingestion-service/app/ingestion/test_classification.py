from uuid import UUID

from app.ingestion.services.file_classifier import (
    FileClassificationService
)


if __name__ == "__main__":

    job_id = UUID("12ec60f7-7e01-4947-a2fb-e9b202253e3e")

    classifier = FileClassificationService()

    classifier.classify_files(job_id)
