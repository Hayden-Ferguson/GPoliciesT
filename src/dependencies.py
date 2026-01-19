"""Dependency injection for FastAPI routes."""

from functools import lru_cache

from src.config.logging import get_logger
from src.config.settings import Settings, get_settings
from src.services.ingest import IngestionService
from src.services.llm import LLMClient
from src.services.agent import AgentService
from src.services.vector_store import VectorStore
from src.config.settings import LLMProvider
from langchain_core.language_models.chat_models import BaseChatModel


logger = get_logger(__name__)

def get_config() -> Settings:
    """Get cached settings instance for dependency injection."""
    return get_settings()

# TODO: Implement actual dependencies below

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
        DB_URI=settings.database_uri,
    )