
import hashlib
from unittest.mock import Mock
from uuid import uuid4

import pytest

from app import documents


def setup_document_test(monkeypatch, tmp_path):
    """Prepare an isolated document-processing test environment."""

    file_id = uuid4()
    source = tmp_path / "sample.txt"
    source.write_text("Sample document content", encoding="utf-8")

    checksum = hashlib.sha256(source.read_bytes()).hexdigest()

    document = {
        "file_id": str(file_id),
        "relative_path": "sample.txt",
        "file_name": "sample.txt",
        "file_type": "TEXT",
        "checksum": checksum,
    }

    markdown_directory = tmp_path / "markdown"

    monkeypatch.setattr(documents, "MARKDOWN_DIRECTORY", markdown_directory)
    monkeypatch.setattr(
        documents,
        "resolve_source",
        lambda relative_path, file_type: source,
    )
    monkeypatch.setattr(
        documents,
        "has_unchanged_chunks",
        lambda file_id, checksum: False,
    )

    save_mock = Mock()
    clear_mock = Mock()

    monkeypatch.setattr(documents, "save_chunks", save_mock)
    monkeypatch.setattr(documents, "clear_document_chunks", clear_mock)

    return document, save_mock, clear_mock


def test_empty_extraction_preserves_existing_chunks(monkeypatch, tmp_path):
    document, save_mock, clear_mock = setup_document_test(
        monkeypatch, tmp_path
    )

    def empty_extraction(document, source):
        raise ValueError("Document extraction produced no usable content.")

    monkeypatch.setattr(documents, "convert_document", empty_extraction)

    with pytest.raises(ValueError, match="no usable content"):
        documents.process_document(document)

    save_mock.assert_not_called()
    clear_mock.assert_not_called()


def test_empty_chunks_preserve_existing_chunks(monkeypatch, tmp_path):
    document, save_mock, clear_mock = setup_document_test(
        monkeypatch, tmp_path
    )

    monkeypatch.setattr(
        documents,
        "convert_document",
        lambda document, source: "# Sample\n\nSample content",
    )
    monkeypatch.setattr(
        documents,
        "chunk_markdown_file",
        lambda path: [],
    )

    with pytest.raises(ValueError, match="no usable chunks"):
        documents.process_document(document)

    save_mock.assert_not_called()
    clear_mock.assert_not_called()


def test_empty_embeddings_preserve_existing_chunks(monkeypatch, tmp_path):
    document, save_mock, clear_mock = setup_document_test(
        monkeypatch, tmp_path
    )

    chunk = {
        "content": "Sample document content",
        "metadata": {},
    }

    monkeypatch.setattr(
        documents,
        "convert_document",
        lambda document, source: "# Sample\n\nSample content",
    )
    monkeypatch.setattr(
        documents,
        "chunk_markdown_file",
        lambda path: [chunk.copy() | {"metadata": {}}],
    )
    monkeypatch.setattr(
        documents,
        "generate_embeddings",
        lambda contents: [],
    )

    with pytest.raises(ValueError, match="Embedding count or dimension"):
        documents.process_document(document)

    save_mock.assert_not_called()
    clear_mock.assert_not_called()


def test_successful_processing_saves_chunks(monkeypatch, tmp_path):
    document, save_mock, clear_mock = setup_document_test(
        monkeypatch, tmp_path
    )

    chunk = {
        "content": "Sample document content",
        "metadata": {},
    }

    monkeypatch.setattr(
        documents,
        "convert_document",
        lambda document, source: "# Sample\n\nSample content",
    )
    monkeypatch.setattr(
        documents,
        "chunk_markdown_file",
        lambda path: [chunk.copy() | {"metadata": {}}],
    )
    monkeypatch.setattr(
        documents,
        "generate_embeddings",
        lambda contents: [[0.1] * 768],
    )

    result = documents.process_document(document)

    assert result["status"] == "processed"
    assert result["chunks"] == 1
    assert result["embeddings"] == 1

    save_mock.assert_called_once()
    clear_mock.assert_not_called()
