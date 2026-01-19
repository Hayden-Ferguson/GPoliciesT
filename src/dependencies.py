"""Dependency injection for FastAPI routes."""

from functools import lru_cache

from src.config.logging import get_logger
from src.config.settings import Settings, get_settings, LLMProvider, CheckpointType
from src.services.ingest import IngestionService
from src.services.llm import LLMClient
from src.services.agent import AgentService
from src.services.vector_store import VectorStore
from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.checkpoint.memory import InMemorySaver


logger = get_logger(__name__)

def get_config() -> Settings:
    """Get cached settings instance for dependency injection."""
    return get_settings()

# Global checkpointer
checkpointer = None
checkpointer_contex = None

async def init_checkpointer():
    """Initialize checkpointer based on settings. Called during app startup."""
    global checkpointer, checkpointer_contex
    settings = get_settings()

    if settings.checkpoint_type == CheckpointType.MEMORY:
        checkpointer = InMemorySaver()
        logger.info("Checkpoint initialized")
    elif settings.checkpoint_type == CheckpointType.POSTGRES:
        if not settings.database_uri:
            raise ValueError(
                "checkpoint_postgres_url must be set when using postgres checkpoint type"
            )
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        
        checkpointer_contex = AsyncPostgresSaver.from_conn_string(settings.database_uri)
        checkpointer = await checkpointer_contex.__aenter__()
        await _checkpointer.setup()
        logger.info("AsyncPostgresSaver initialized")
    else:
        raise ValueError(f"Invalid checkpoint type: {settings.checkpoint_type}")


async def cleanup_checkpointer():
    """Cleanup checkpointer. Called during app shutdown."""
    global checkpointer, checkpointer_contex
    if checkpointer_contex is not None:
        await checkpointer_contex.__aexit__(None, None, None)
        logger.info("AsyncPostgresSaver closed")
    checkpointer = None
    checkpointer_contex = None


def get_checkpointer():
    """Get checkpointer."""
    if checkpointer is None:
        raise RuntimeError("Checkpointer not initialized. Call init_checkpointer() first.")
    return checkpointer


@lru_cache
def get_vector_store() -> VectorStore:
    '''Provide ChromaDB vector store instance'''
    settings = get_settings()
    return VectorStore(
        client_type=settings.chroma_client_type,
        collection_name=settings.chroma_collection_name,
        persist_path=settings.chroma_persist_path,
        host=settings.chroma_host,
        port=settings.chroma_port,
        chroma_cloud_api_key=settings.chroma_cloud_api_key,
        chroma_tenant_id=settings.chroma_tenant_id,
        chroma_database=settings.chroma_database,
    )

def get_ingest_service() -> IngestionService:
    """Provide ingest service instance."""
    settings = get_settings()
    return IngestionService(
        vector_store=get_vector_store(),
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )

@lru_cache
def get_llm()  -> BaseChatModel:
    """Create the underlying LangChain model."""

    import boto3
    from langchain_aws import ChatBedrock

    settings = get_settings()

    if settings.llm_provider == LLMProvider.BEDROCK:
        import boto3
        from langchain_aws import ChatBedrock

        if not settings.aws_access_key_id or not settings.aws_secret_access_key:
            raise ValueError("AWS credentials are required for Bedrock provider.")

        client = boto3.client(
            "bedrock-runtime",
            region_name=settings.aws_region or "us-west-2",
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
        model = ChatBedrock(
            model_id=settings.llm_model,
            client=client,
            model_kwargs={
                "temperature": settings.llm_temperature,
                "max_tokens": settings.llm_max_tokens,
            },
        )
    else:
        from langchain_openai import ChatOpenAI
        
        model = ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.llm_api_key,
            temperature=settings.llm_temperature,
            base_url=settings.llm_base_url or None,
            max_tokens=settings.llm_max_tokens,
        )
    logger.info("LLM Model created")

    return model

def get_agent_service() -> AgentService:
    """Provide Agent service instance."""
    settings = get_settings()
    return AgentService(
        llm=get_llm(),
        vector_store=get_vector_store(),
        checkpointer=get_checkpointer(),
    )