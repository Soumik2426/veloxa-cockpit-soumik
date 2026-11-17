from app.ingestion.create_ingestion_job import create_ingestion_job
from app.ingestion.pipeline import UnifiedIngestionPipeline


def run_ingestion():

    print("\n========== VELOXA DATA PIPELINE ==========\n")

    # Create a new ingestion job
    source_id, job_id = create_ingestion_job()

    # Initialize and execute unified pipeline
    pipeline = UnifiedIngestionPipeline()

    result = pipeline.run(
        source_id=source_id,
        job_id=job_id
    )

    print("\n========== PIPELINE SUMMARY ==========\n")
    print(result)


if __name__ == "__main__":
    run_ingestion()
