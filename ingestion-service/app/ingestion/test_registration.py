from uuid import UUID

from app.ingestion.services.file_registration import FileRegistrationService


if __name__ == "__main__":

    source_id = UUID("c1025d4d-2af0-450a-8109-ddb3b8e3db52")
    job_id = UUID("12ec60f7-7e01-4947-a2fb-e9b202253e3e")

    registration_service = FileRegistrationService()

    registration_service.register_files(
        source_id=source_id,
        job_id=job_id
    )
