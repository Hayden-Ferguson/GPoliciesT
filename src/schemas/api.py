"""API request/response schemas."""

from pydantic import BaseModel, Field


# --- Query Schemas ---

class QueryRequest(BaseModel):
    """Request to query the RAG system."""

    question: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Question to ask about product reviews",
        examples=["What are the policies on drugs?"],
    )
    thread_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="What thread are you using?",
        examples=["thread_001"],
    )


class QueryResponse(BaseModel):
    """Response from RAG query."""

    answer: str
    #sources: list[str]
    #thread_id: str


# --- Ingest Schemas ---


class IngestStatsResponse(BaseModel):
    """Response with ingestion statistics."""

    total_documents: int
    unique_categories: int
    unique_apps: int
    categories: list[str] | str


# --- Health Schemas ---

class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    service: str
    documents: int


# --- Model Info ---

class ModelInfoResponse(BaseModel):
    """LLM model information."""

    provider: str
    model: str
    temperature: float
    max_tokens: int