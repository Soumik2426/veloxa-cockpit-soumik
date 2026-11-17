from app.database.session import SessionLocal
from app.ingestion.models import IngestionFile, IngestionJob
from app.discovery.file_discovery import FileDiscoveryService
from app.ingestion.services.file_fingerprint import FileFingerprintService


class FileRegistrationService:

    def __init__(self):
        self.discovery_service = FileDiscoveryService()
        self.fingerprint_service = FileFingerprintService()

    def register_files(self, source_id, job_id):

        db = SessionLocal()

        try:
            # Step 1: Discover all files
            files = self.discovery_service.discover_files()

            registered_count = 0
            duplicate_count = 0

            # Step 2: Find the ingestion job
            job = (
                db.query(IngestionJob)
                .filter(IngestionJob.id == job_id)
                .first()
            )

            if job is None:
                raise ValueError("Ingestion job not found.")

            # Step 3: Process each discovered file
            for file_path in files:

                # Calculate SHA-256 checksum
                checksum = self.fingerprint_service.calculate_checksum(
                    file_path
                )

                # Get relative file path
                relative_path = str(
                    file_path.relative_to(
                        self.discovery_service.input_directory
                    )
                ).replace("\\", "/")

                # Check whether this exact file version is already registered
                existing_file = (
                    db.query(IngestionFile)
                    .filter(
                        IngestionFile.source_connection_id == source_id,
                        IngestionFile.relative_path == relative_path,
                        IngestionFile.checksum == checksum
                    )
                    .first()
                )

                if existing_file:
                    existing_file.ingestion_job_id = job_id
                    duplicate_count += 1
                    continue

                # Find the previous version of this file
                previous_version = (
                    db.query(IngestionFile)
                    .filter(
                        IngestionFile.source_connection_id == source_id,
                        IngestionFile.relative_path == relative_path
                    )
                    .order_by(IngestionFile.version.desc())
                    .first()
                )

                # Assign version number
                version = (
                    previous_version.version + 1
                    if previous_version
                    else 1
                )

                # Create ingestion file record
                ingestion_file = IngestionFile(
                    source_connection_id=source_id,
                    ingestion_job_id=job_id,
                    file_name=file_path.name,
                    relative_path=relative_path,
                    file_extension=file_path.suffix.lower(),
                    file_type="UNKNOWN",
                    checksum=checksum,
                    file_size=file_path.stat().st_size,
                    status="DISCOVERED",
                    version=version
                )

                db.add(ingestion_file)
                registered_count += 1

            # Step 4: Update ingestion job statistics
            job.discovered_count = len(files)

            # Step 5: Commit everything to PostgreSQL
            db.commit()

            print("\nFile registration completed!")
            print(f"Discovered files: {len(files)}")
            print(f"Newly registered: {registered_count}")
            print(f"Already registered: {duplicate_count}")

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()
