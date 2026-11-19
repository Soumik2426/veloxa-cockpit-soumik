from unittest.mock import MagicMock, patch

from app.rag.retriever import retrieve_relevant_chunks


def run_retrieval_with_scores(scores):
    rows = [
        (
            f"chunk-{index}",
            f"Test content {index}",
            {
                "source_file": f"document-{index}.pdf",
                "source_path": f"/documents/document-{index}.pdf",
                "document_type": "pdf",
                "section": "Test section",
            },
            score,
        )
        for index, score in enumerate(scores, start=1)
    ]

    mock_connection = MagicMock()
    mock_cursor = mock_connection.cursor.return_value.__enter__.return_value
    mock_cursor.fetchall.return_value = rows

    with (
        patch(
            "app.rag.retriever.generate_embedding",
            return_value=[0.1] * 768,
        ),
        patch(
            "app.rag.retriever.get_connection",
            return_value=mock_connection,
        ),
    ):
        results = retrieve_relevant_chunks("Test question")

    mock_connection.close.assert_called_once()
    return results


def test_retriever_keeps_relevant_chunks():
    results = run_retrieval_with_scores([0.69, 0.64])

    assert len(results) == 2
    assert all(result["similarity"] >= 0.58 for result in results)


def test_retriever_rejects_irrelevant_chunks():
    results = run_retrieval_with_scores([0.54, 0.52])

    assert results == []


def test_retriever_filters_mixed_results():
    results = run_retrieval_with_scores([0.69, 0.55, 0.63, 0.53])

    assert len(results) == 2
    assert [result["similarity"] for result in results] == [0.69, 0.63]


def test_retriever_returns_empty_when_no_chunks_exist():
    results = run_retrieval_with_scores([])

    assert results == []
