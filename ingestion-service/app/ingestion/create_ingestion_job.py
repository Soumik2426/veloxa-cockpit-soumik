from app.database.session import SessionLocal
from app.ingestion.models import SourceConnection, IngestionJob


def create_ingestion_job():
    db = SessionLocal()

    try:
        # Check whether this source is already registered
        source = (
            db.query(SourceConnection)
            .filter(
                SourceConnection.name == "Veloxa Company Data Room",
                SourceConnection.connector_type == "LOCAL_FILESYSTEM"
            )
            .first()
        )

        # Register the source if it doesn't exist
        if source is None:
            source = SourceConnection(
                name="Veloxa Company Data Room",
                connector_type="LOCAL_FILESYSTEM",
                config={
                    "input_directory": "../data/input/Veloxa_Hackathon_Release_Packs"
                },
                status="ACTIVE"
            )

            db.add(source)
            db.flush()

            print("Source connection registered.")

        else:
            print("Source connection already exists.")

        # Create a new ingestion job
        job = IngestionJob(
            source_connection_id=source.id,
            status="PENDING",
            trigger_type="MANUAL"
        )

        db.add(job)

        # Flush to generate the database-generated UUID
        db.flush()

        # Capture IDs after flushing
        source_id = source.id
        job_id = job.id

        db.commit()

        print("\nIngestion job created successfully!")
        print(f"Source ID: {source_id}")
        print(f"Job ID: {job_id}")
        print(f"Job Status: {job.status}")

        return source_id, job_id

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    create_ingestion_job()
