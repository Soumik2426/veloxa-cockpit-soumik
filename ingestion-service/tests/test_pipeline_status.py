
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

from app.ingestion import pipeline as pipeline_module


def setup_pipeline_test(monkeypatch, records):
    """Create a mocked database session without connecting to PostgreSQL."""
    mock_session = MagicMock()

    mock_session.query.return_value.filter.return_value.all.return_value = records

    monkeypatch.setattr(
        pipeline_module,
        "SessionLocal",
        lambda: mock_session,
    )

    pipeline = pipeline_module.UnifiedIngestionPipeline.__new__(
        pipeline_module.UnifiedIngestionPipeline
    )

    return pipeline, mock_session


def test_processed_document_updates_status(monkeypatch):
    file_id = uuid4()
    record = SimpleNamespace(
        id=file_id,
        status="PROCESSING",
        processed_at=None,
    )

    pipeline, session = setup_pipeline_test(monkeypatch, [record])

    documents = [{"file_id": str(file_id)}]
    results = [{"file_id": str(file_id), "status": "processed"}]

    pipeline._update_document_statuses(documents, results)

    assert record.status == "PROCESSED"
    assert record.processed_at is not None
    session.commit.assert_called_once()


def test_skipped_unchanged_preserves_existing_timestamp(monkeypatch):
    file_id = uuid4()
    existing_timestamp = datetime(2026, 11, 18, tzinfo=timezone.utc)

    record = SimpleNamespace(
        id=file_id,
        status="PROCESSING",
        processed_at=existing_timestamp,
    )

    pipeline, session = setup_pipeline_test(monkeypatch, [record])

    documents = [{"file_id": str(file_id)}]
    results = [{"file_id": str(file_id), "status": "skipped_unchanged"}]

    pipeline._update_document_statuses(documents, results)

    assert record.status == "PROCESSED"
    assert record.processed_at == existing_timestamp
    session.commit.assert_called_once()


def test_failed_document_updates_status(monkeypatch):
    file_id = uuid4()
    record = SimpleNamespace(
        id=file_id,
        status="PROCESSING",
        processed_at=None,
    )

    pipeline, session = setup_pipeline_test(monkeypatch, [record])

    documents = [{"file_id": str(file_id)}]
    results = [{"file_id": str(file_id), "status": "failed"}]

    pipeline._update_document_statuses(documents, results)

    assert record.status == "FAILED"
    assert record.processed_at is None
    session.commit.assert_called_once()


def test_missing_ai_result_marks_document_failed(monkeypatch):
    file_id = uuid4()
    record = SimpleNamespace(
        id=file_id,
        status="PROCESSING",
        processed_at=None,
    )

    pipeline, session = setup_pipeline_test(monkeypatch, [record])

    documents = [{"file_id": str(file_id)}]
    results = []

    pipeline._update_document_statuses(documents, results)

    assert record.status == "FAILED"
    session.commit.assert_called_once()
