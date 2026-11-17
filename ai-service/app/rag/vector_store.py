import os
from uuid import UUID

import psycopg
from dotenv import load_dotenv
from pgvector.psycopg import register_vector
from psycopg.types.json import Jsonb


load_dotenv()


def get_connection():

    connection = psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "veloxa_cockpit"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD")
    )

    register_vector(connection)

    return connection


def save_chunks(chunks: list[dict]):

    if not chunks:
        print("No chunks to store.")
        return

    # Validate the data before opening the transaction.
    file_ids = set()

    for chunk in chunks:
        metadata = chunk["metadata"]

        file_id = UUID(metadata["source_file_id"])
        file_ids.add(file_id)

        if len(chunk["embedding"]) != 768:
            raise ValueError(
                f"Invalid embedding dimensions for chunk "
                f"{chunk['chunk_index']}"
            )

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            # A changed file is registered with a new ingestion_file UUID.
            # Replace any prior version of the same source path atomically.
            source_paths = {
                chunk["metadata"].get("source_path")
                for chunk in chunks
                if chunk["metadata"].get("source_path")
            }
            for source_path in source_paths:
                cursor.execute(
                    """
                    DELETE FROM document_chunks
                    WHERE metadata->>'source_path' = %s
                    """,
                    (source_path,),
                )

            # Remove previous chunks for these documents.
            # The replacement happens in the same transaction.
            for file_id in file_ids:
                cursor.execute(
                    """
                    DELETE FROM document_chunks
                    WHERE ingestion_file_id = %s
                    """,
                    (file_id,)
                )

            # Insert the latest chunks.
            for chunk in chunks:

                metadata = chunk["metadata"]

                cursor.execute(
                    """
                    INSERT INTO document_chunks (
                        ingestion_file_id,
                        chunk_index,
                        content,
                        metadata,
                        embedding
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        UUID(metadata["source_file_id"]),
                        chunk["chunk_index"],
                        chunk["content"],
                        Jsonb(metadata),
                        chunk["embedding"]
                    )
                )

        connection.commit()

        print(f"Successfully stored {len(chunks)} chunks.")
        print(f"Documents processed: {len(file_ids)}")

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
