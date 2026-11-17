from typing import Literal
from uuid import UUID

from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.documents import process_document


class DocumentReference(BaseModel):
    file_id: UUID
    file_name: str = Field(min_length=1)
    relative_path: str = Field(min_length=1)
    file_type: Literal["PDF", "WORD", "TEXT", "EMAIL"]
    checksum: str = Field(min_length=1, max_length=64)
    job_id: UUID


class DocumentBatch(BaseModel):
    job_id: UUID
    documents: list[DocumentReference]


app = FastAPI(title="Veloxa AI Service")


@app.post("/api/v1/documents/process")
def process_documents(batch: DocumentBatch):
    results = []
    for document in batch.documents:
        data = document.model_dump(mode="json")
        if document.job_id != batch.job_id:
            results.append({
                "file_id": str(document.file_id),
                "status": "failed",
                "error": "Document job_id does not match batch job_id",
            })
            continue
        try:
            results.append(process_document(data))
        except Exception as error:
            results.append({
                "file_id": str(document.file_id),
                "file_name": document.file_name,
                "relative_path": document.relative_path,
                "status": "failed",
                "error": str(error),
            })

    successful = [item for item in results if item["status"] != "failed"]
    return {
        "documents_received": len(results),
        "successfully_processed": len(successful),
        "skipped_unchanged": sum(item["status"] == "skipped_unchanged" for item in successful),
        "chunks_generated": sum(item.get("chunks", 0) for item in successful),
        "embeddings_generated": sum(item.get("embeddings", 0) for item in successful),
        "failed_documents": [item for item in results if item["status"] == "failed"],
        "documents": results,
    }
