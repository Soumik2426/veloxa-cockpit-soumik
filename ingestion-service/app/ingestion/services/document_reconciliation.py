import logging
from uuid import UUID

from sqlalchemy import bindparam, text

from app.database.session import SessionLocal


logger = logging.getLogger(__name__)

UNSTRUCTURED_TYPES = ("PDF", "WORD", "TEXT", "EMAIL")


class DocumentReconciliationService:
    """
    Reconcile stale ingestion_file statuses using existing document chunks.

    This service does not generate embeddings, call the AI service,
    or modify document_chunks.
    """

    def reconcile_job(
        self,
        job_id: UUID,
        dry_run: bool = True,
    ) -> dict:
        db = SessionLocal()

        report = {
            "job_id": str(job_id),
            "dry_run": dry_run,
            "total_documents": 0,
            "reconciled": [],
            "already_processed": [],
            "missing_chunks": [],
            "checksum_mismatches": [],
            "other_statuses": [],
        }

        try:
            query = text("""
                SELECT
                    f.id,
                    f.file_name,
                    f.status,
                    COUNT(dc.id) AS chunk_count,
                    COUNT(dc.id) FILTER (
                        WHERE dc.metadata->>'checksum' = f.checksum
                    ) AS matching_chunk_count
                FROM ingestion_file f
                LEFT JOIN document_chunks dc
                    ON dc.ingestion_file_id = f.id
                WHERE f.ingestion_job_id = :job_id
                  AND f.file_type IN :file_types
                GROUP BY
                    f.id,
                    f.file_name,
                    f.status,
                    f.checksum
                ORDER BY f.file_name
            """).bindparams(
                bindparam("file_types", expanding=True)
            )

            result = db.execute(
                query,
                {
                    "job_id": job_id,
                    "file_types": list(UNSTRUCTURED_TYPES),
                },
            )

            documents = result.mappings().all()
            report["total_documents"] = len(documents)

            for document in documents:
                file_id = document["id"]
                file_name = document["file_name"]
                status = document["status"]
                chunk_count = document["chunk_count"]
                matching_count = document["matching_chunk_count"]

                # No existing chunks.
                if chunk_count == 0:
                    report["missing_chunks"].append(file_name)
                    continue

                # Every chunk must have the registered checksum.
                if matching_count != chunk_count:
                    report["checksum_mismatches"].append(file_name)
                    continue

                # Already reconciled.
                if status == "PROCESSED":
                    report["already_processed"].append(file_name)
                    continue

                # Only DISCOVERED records are eligible.
                if status != "DISCOVERED":
                    report["other_statuses"].append({
                        "file_name": file_name,
                        "status": status,
                    })
                    continue

                # Record the candidate in both dry-run and live modes.
                report["reconciled"].append(file_name)

                if not dry_run:
                    db.execute(
                        text("""
                            UPDATE ingestion_file
                            SET
                                status = 'PROCESSED',
                                processed_at = COALESCE(
                                    processed_at,
                                    now()
                                )
                            WHERE id = :file_id
                              AND status = 'DISCOVERED'
                        """),
                        {"file_id": file_id},
                    )

            if dry_run:
                db.rollback()
            else:
                db.commit()

            logger.info(
                "Document reconciliation completed for job %s "
                "(dry_run=%s)",
                job_id,
                dry_run,
            )

            return report

        except Exception:
            db.rollback()
            logger.exception(
                "Document reconciliation failed for job %s",
                job_id,
            )
            raise

        finally:
            db.close()
