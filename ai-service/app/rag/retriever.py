import os
from pgvector import Vector
from app.rag.embeddings import generate_embedding
from app.rag.vector_store import get_connection

MIN_SIMILARITY = float(
    os.getenv("RAG_MIN_SIMILARITY", "0.58")
)


def retrieve_relevant_chunks(
    question: str,
    top_k: int = 5
) -> list[dict]:

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    if not 1 <= top_k <= 20:
        raise ValueError("top_k must be between 1 and 20.")

    print(f"\nSearching for: {question}")

    # Step 1: Convert the question into an embedding.
    query_embedding = generate_embedding(
        question,
        task_type="RETRIEVAL_QUERY"
    )

    # Step 2: Search PostgreSQL using cosine distance.
    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            vector = Vector(query_embedding)

            cursor.execute(
                """
                SELECT id,
                       content,
                       metadata,
                       1 - (embedding <=> %s) AS similarity
                FROM document_chunks
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> %s
                    LIMIT %s
                """,
                (
                    vector,
                    vector,
                    top_k
                )
            )

            rows = cursor.fetchall()

        results = []

        for row in rows:

            chunk_id, content, metadata, similarity = row
            similarity = float(similarity)

            if similarity < MIN_SIMILARITY:
                continue

            results.append({
                "chunk_id": str(chunk_id),
                "content": content,
                "source_file": metadata.get("source_file"),
                "source_path": metadata.get("source_path"),
                "document_type": metadata.get("document_type"),
                "section": metadata.get("section"),
                "similarity": similarity
            })

        return results

    finally:
        connection.close()


if __name__ == "__main__":

    question = (
        "What are the major problems affecting "
        "the engineering team's delivery?"
    )

    results = retrieve_relevant_chunks(question, top_k=5)

    print("\n========== RETRIEVAL RESULTS ==========\n")

    for index, result in enumerate(results, start=1):

        print(f"\nResult {index}")
        print(f"Source: {result['source_file']}")
        print(f"Section: {result['section']}")
        print(f"Similarity: {result['similarity']:.4f}")
        print(f"Content: {result['content'][:500]}")
        print("-" * 60)
