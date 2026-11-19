import logging
import time
from typing import Literal
from uuid import UUID

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.agent.orchestrator import GeminiServiceError, answer_question
from app.agent.schemas import AgentAskRequest, AgentResponse
from app.documents import process_document


# --------------------------------------------------
# LOGGING CONFIGURATION
# --------------------------------------------------

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    force=True,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# --------------------------------------------------
# FASTAPI APPLICATION
# --------------------------------------------------

app = FastAPI(title="Veloxa AI Service")


# --------------------------------------------------
# HTTP REQUEST LOGGING MIDDLEWARE
# --------------------------------------------------

@app.middleware("http")
async def log_http_requests(request, call_next):
    start_time = time.perf_counter()

    try:
        response = await call_next(request)

        duration_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            "HTTP REQUEST | method=%s | path=%s | "
            "status_code=%d | duration=%.2f ms",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )

        return response

    except Exception:
        duration_ms = (time.perf_counter() - start_time) * 1000

        logger.exception(
            "HTTP REQUEST FAILED | method=%s | path=%s | "
            "duration=%.2f ms",
            request.method,
            request.url.path,
            duration_ms,
        )

        raise


# --------------------------------------------------
# DOCUMENT REQUEST MODELS
# --------------------------------------------------

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


# --------------------------------------------------
# AGENT QUESTION ENDPOINT
# --------------------------------------------------

@app.post("/api/v1/agent/ask", response_model=AgentResponse)
def ask_agent(request: AgentAskRequest):
    start_time = time.perf_counter()

    logger.info(
        "Agent request received | question_length=%d",
        len(request.question),
    )

    try:
        response = answer_question(request.question)

        elapsed = time.perf_counter() - start_time

        logger.info(
            "Agent request completed | sources=%s | "
            "confidence=%s | evidence_count=%d | duration=%.2fs",
            response.retrieval_sources,
            response.confidence.level,
            len(response.evidence),
            elapsed,
        )

        return response

    except GeminiServiceError as error:
        elapsed = time.perf_counter() - start_time

        logger.exception(
            "Gemini service failure | duration=%.2fs",
            elapsed,
        )

        raise HTTPException(
            status_code=502,
            detail="The AI agent could not complete the request.",
        ) from error

    except ValueError as error:
        logger.warning(
            "Invalid agent request | error=%s",
            str(error),
        )

        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    except Exception:
        elapsed = time.perf_counter() - start_time

        logger.exception(
            "Unexpected agent failure | duration=%.2fs",
            elapsed,
        )

        raise


# --------------------------------------------------
# DOCUMENT PROCESSING ENDPOINT
# --------------------------------------------------

@app.post("/api/v1/documents/process")
def process_documents(batch: DocumentBatch):

    logger.info(
        "Document processing batch received | job_id=%s | count=%d",
        batch.job_id,
        len(batch.documents),
    )

    results = []

    for document in batch.documents:
        data = document.model_dump(mode="json")

        if document.job_id != batch.job_id:

            logger.warning(
                "Document job ID mismatch | file_id=%s",
                document.file_id,
            )

            results.append({
                "file_id": str(document.file_id),
                "status": "failed",
                "error": "Document job_id does not match batch job_id",
            })

            continue

        try:
            result = process_document(data)

            results.append(result)

            logger.info(
                "Document processed | file_name=%s | "
                "status=%s | chunks=%s",
                document.file_name,
                result.get("status"),
                result.get("chunks", 0),
            )

        except Exception as error:

            logger.exception(
                "Document processing failed | file_name=%s",
                document.file_name,
            )

            results.append({
                "file_id": str(document.file_id),
                "file_name": document.file_name,
                "relative_path": document.relative_path,
                "status": "failed",
                "error": str(error),
            })

    successful = [
        item for item in results
        if item["status"] != "failed"
    ]

    failed = [
        item for item in results
        if item["status"] == "failed"
    ]

    response = {
        "documents_received": len(results),

        "successfully_processed": len(successful),

        "skipped_unchanged": sum(
            item["status"] == "skipped_unchanged"
            for item in successful
        ),

        "chunks_generated": sum(
            item.get("chunks", 0)
            for item in successful
        ),

        "embeddings_generated": sum(
            item.get("embeddings", 0)
            for item in successful
        ),

        "failed_documents": failed,

        "documents": results,
    }

    logger.info(
        "Document batch completed | job_id=%s | "
        "successful=%d | failed=%d",
        batch.job_id,
        len(successful),
        len(failed),
    )

    return response
