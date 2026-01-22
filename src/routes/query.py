"""Query routes."""

from fastapi import APIRouter, Depends, HTTPException
from uuid import uuid4

from src.config.logging import get_logger
from src.dependencies import get_llm, get_agent_service
from src.schemas.api import ModelInfoResponse, QueryRequest, QueryResponse, ThreadResponse
from src.services.llm import LLMClient
from src.services.agent import AgentService

logger = get_logger(__name__)

router = APIRouter(prefix="/query", tags=["query"])


@router.post("", response_model=QueryResponse)
def query(
    request: QueryRequest,
    agent_service: AgentService = Depends(get_agent_service),
) -> QueryResponse:
    """Query the RAG system with a question."""
    logger.info(f"Query: {request.question[:50]}...")

    try:
        result = agent_service.query(
            question=request.question,
            thread_id=request.thread_id,
        )
        return QueryResponse(**result)
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/threads", response_model=ThreadResponse)
def create_thread() -> ThreadResponse:
    """Create a new thread."""
    thread_id = f"thread_{uuid4()}"
    logger.debug(f"Created new thread: {thread_id}")
    return ThreadResponse(thread_id=thread_id)

'''
@router.get("/model", response_model=ModelInfoResponse)
def get_model_info(
    llm: LLMClient = Depends(get_llm),
) -> ModelInfoResponse:
    """Get current LLM model information."""
    return ModelInfoResponse(**llm.get_model_info())
'''