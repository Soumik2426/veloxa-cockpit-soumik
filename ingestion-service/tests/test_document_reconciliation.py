
from uuid import uuid4
from unittest.mock import MagicMock

from app.ingestion.services.document_reconciliation import (
    DocumentReconciliationService,
)


def make_document(
    file_name,
    status="DISCOVERED",
    chunk_count=2,
    matching_chunk_count=2,
):
    return {
        "id": uuid4(),
        "file_name": file_name,
        "status": status,
        "chunk_count": chunk_count,
        "matching_chunk_count": matching_chunk_count,
    }


def mock_database(monkeypatch, documents):
    db = MagicMock()

    select_result = MagicMock()
    select_result.mappings.return_value.all.return_value = documents
    db.execute.return_value = select_result

    monkeypatch.setattr(
        "app.ingestion.services.document_reconciliation.SessionLocal",
        lambda: db,
    )

    return db


def test_dry_run_does_not_update_database(monkeypatch):
    documents = [
        make_document("report.pdf"),
        make_document("README.txt", status="PROCESSED"),
    ]
    db = mock_database(monkeypatch, documents)

    report = DocumentReconciliationService().reconcile_job(
        uuid4(),
        dry_run=True,
    )

    assert report["total_documents"] == 2
    assert report["reconciled"] == ["report.pdf"]
    assert report["already_processed"] == ["README.txt"]

    # Only the SELECT query should execute.
    assert db.execute.call_count == 1
    db.rollback.assert_called_once()
    db.commit.assert_not_called()


def test_live_reconciliation_updates_eligible_files(monkeypatch):
    documents = [
        make_document("report.pdf"),
        make_document("notes.docx"),
    ]
    db = mock_database(monkeypatch, documents)

    report = DocumentReconciliationService().reconcile_job(
        uuid4(),
        dry_run=False,
    )

    assert report["reconciled"] == ["report.pdf", "notes.docx"]

    # One SELECT plus two UPDATE statements.
    assert db.execute.call_count == 3
    db.commit.assert_called_once()
    db.rollback.assert_not_called()


def test_already_processed_file_is_not_updated(monkeypatch):
    documents = [
        make_document("README.txt", status="PROCESSED"),
    ]
    db = mock_database(monkeypatch, documents)

    report = DocumentReconciliationService().reconcile_job(
        uuid4(),
        dry_run=False,
    )

    assert report["already_processed"] == ["README.txt"]
    assert report["reconciled"] == []

    # Only the SELECT query should execute.
    assert db.execute.call_count == 1
    db.commit.assert_called_once()


def test_missing_chunks_and_checksum_mismatches_are_skipped(monkeypatch):
    documents = [
        make_document(
            "missing.pdf",
            chunk_count=0,
            matching_chunk_count=0,
        ),
        make_document(
            "mismatch.docx",
            chunk_count=2,
            matching_chunk_count=1,
        ),
    ]
    db = mock_database(monkeypatch, documents)

    report = DocumentReconciliationService().reconcile_job(
        uuid4(),
        dry_run=False,
    )

    assert report["missing_chunks"] == ["missing.pdf"]
    assert report["checksum_mismatches"] == ["mismatch.docx"]
    assert report["reconciled"] == []

    # Neither file should receive an UPDATE.
    assert db.execute.call_count == 1
    db.commit.assert_called_once()
