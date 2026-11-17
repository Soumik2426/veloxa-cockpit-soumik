from app.database.session import SessionLocal
from app.ingestion.models import IngestionFile


class FileClassificationService:

    FILE_TYPE_MAP = {
        ".xlsx": "EXCEL",
        ".xls": "EXCEL",
        ".pdf": "PDF",
        ".docx": "WORD",
        ".doc": "WORD",
        ".eml": "EMAIL",
        ".csv": "CSV",
        ".txt": "TEXT"
    }

    def classify_files(self, job_id):

        db = SessionLocal()

        try:
            files = (
                db.query(IngestionFile)
                .filter(IngestionFile.ingestion_job_id == job_id)
                .all()
            )

            classified_count = 0
            unknown_count = 0

            for file in files:

                extension = file.file_extension.lower()

                file_type = self.FILE_TYPE_MAP.get(
                    extension,
                    "UNKNOWN"
                )

                file.file_type = file_type

                if file_type == "UNKNOWN":
                    unknown_count += 1
                else:
                    classified_count += 1

            db.commit()

            print("\nFile classification completed!")
            print(f"Total files: {len(files)}")
            print(f"Classified files: {classified_count}")
            print(f"Unknown files: {unknown_count}")

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()
