from pathlib import Path

from app.rag.chunker import chunk_markdown_directory
from app.rag.embeddings import generate_embeddings
from app.rag.vector_store import save_chunks


BATCH_SIZE = 10


def run_rag_pipeline():

    print("\n========== RAG PIPELINE STARTED ==========\n")

    # Locate the Markdown directory.
    project_root = Path(__file__).resolve().parents[3]

    markdown_directory = (
        project_root / "data" / "processed" / "markdown"
    )

    if not markdown_directory.exists():
        raise FileNotFoundError(
            f"Markdown directory not found: {markdown_directory}"
        )

    # Stage 1: Generate chunks.
    print("\n========== CHUNK GENERATION ==========\n")

    chunks = chunk_markdown_directory(markdown_directory)

    if not chunks:
        print("No chunks found. Stopping pipeline.")
        return

    print(f"\nTotal chunks: {len(chunks)}")

    # Stage 2: Generate embeddings in batches.
    print("\n========== EMBEDDING GENERATION ==========\n")

    processed_chunks = []

    for start in range(0, len(chunks), BATCH_SIZE):

        batch = chunks[start:start + BATCH_SIZE]

        texts = [
            chunk["content"]
            for chunk in batch
        ]

        embeddings = generate_embeddings(texts)

        if len(embeddings) != len(batch):
            raise ValueError(
                "Embedding count does not match chunk count."
            )

        for chunk, embedding in zip(batch, embeddings):

            if len(embedding) != 768:
                raise ValueError(
                    "Unexpected embedding dimension."
                )

            processed_chunks.append({
                **chunk,
                "embedding": embedding
            })

        print(
            f"Embedded {len(processed_chunks)} / {len(chunks)} chunks"
        )

    # Stage 3: Store embeddings in PostgreSQL.
    print("\n========== VECTOR STORAGE ==========\n")

    save_chunks(processed_chunks)

    print("\n========== RAG PIPELINE COMPLETED ==========\n")


if __name__ == "__main__":
    run_rag_pipeline()
