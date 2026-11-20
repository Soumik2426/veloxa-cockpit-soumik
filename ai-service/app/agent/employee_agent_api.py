import logging
import time

from fastapi import APIRouter, HTTPException

from app.agent.orchestrator import (
    GeminiServiceError,
    answer_question,
)
from app.agent.schemas import (
    AgentResponse,
    EmployeeAgentRespondRequest,
)

logger = logging.getLogger(__name__)

employee_agent_router = APIRouter()


@employee_agent_router.post(
    "/api/v1/employee-agents/respond",
    response_model=AgentResponse,
)
def respond_as_employee_agent(
    request: EmployeeAgentRespondRequest,
):
    start_time = time.perf_counter()

    context = request.employee_context

    logger.info(
        "Employee agent request | employee_code=%s | question_length=%d",
        context.employee_code,
        len(request.question),
    )

    try:
        response = answer_question(
            question=request.question,
            employee_context=context.model_dump(mode="json"),
        )

        logger.info(
            "Employee agent request completed | employee_code=%s | "
            "sources=%s | confidence=%s | evidence_count=%d | duration=%.2fs",
            context.employee_code,
            response.retrieval_sources,
            response.confidence.level,
            len(response.evidence),
            time.perf_counter() - start_time,
        )

        return response

    except GeminiServiceError as error:
        logger.exception(
            "Employee agent AI provider failure | employee_code=%s",
            context.employee_code,
        )

        raise HTTPException(
            status_code=502,
            detail="The employee agent could not complete the request.",
        ) from error

    except ValueError as error:
        logger.warning(
            "Invalid employee agent request | employee_code=%s | error=%s",
            context.employee_code,
            str(error),
        )

        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    except Exception as error:
        logger.exception(
            "Unexpected employee agent failure | employee_code=%s",
            context.employee_code,
        )

        raise HTTPException(
            status_code=500,
            detail="An unexpected employee agent error occurred.",
        ) from error
