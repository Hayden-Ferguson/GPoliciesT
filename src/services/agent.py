"""Agent service."""

from typing import TYPE_CHECKING, Any

from langchain_core.prompts import PromptTemplate
from langchain.agents import create_agent
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.base import BaseCheckpointSaver

from src.config.logging import get_logger
#from src.services.llm import LLMClient
from langchain_core.language_models.chat_models import BaseChatModel
#if TYPE_CHECKING:
from src.services.vector_store import VectorStore


from langchain.tools import tool
from typing import Optional

#from psycopg_pool import ConnectionPool

#pool = ConnectionPool("postgresql://postgres2:postgres2@postgres:5432/postgres2")

logger = get_logger(__name__)


class AgentService:
    """Orchestrates retrieval and generation."""

    def __init__(
        self,
        llm: BaseChatModel,
        vector_store: VectorStore,
        checkpointer: BaseCheckpointSaver,
        k: int = 4,
        DB_URI: str = "",
    ):
        """Initialize RAG service.

        Args:
            llm: LLM client instance.
            vector_store: ChromaDB vector store.
            top_k: Number of documents to retrieve.
            threshold: Distance threshold for filtering.
        """

        self.vector_store = vector_store
        self.k = k

        @tool
        def university_policy_search(
            query: str
        ) -> str:
            """
            Search a database for university policies.

            Args:
            query: semantic search query
            """
            logger.info(f"Tool called! {query} {k}")
            docs = self.vector_store.query(query_text=query, n_results=self.k)
            return "\n\n".join(
                f"[Source: {doc['metadata']['source']}]\n{doc['text']}"
                for doc in docs
            )
        
        logger.info(f"Built tool: {university_policy_search}")

        #cm = PostgresSaver.from_conn_string(DB_URI)
        #checkpointer = cm.__enter__()   
        #checkpointer = PostgresSaver(DB_URI)

        #self._checkpointer_cm = cm

        #checkpointer.setup()  

        self.agent = create_agent(
            model=llm,
            tools=[university_policy_search],
            system_prompt="You are a helpful assistant for searching through Richmond "
            "University policies. Be concise.",
            checkpointer=checkpointer,  # Memory
            name="policy_bot"
        )

        logger.info("Agent created")

    def query(
        self,
        question: str,
        thread_id: str = "test_session",
        #filter_by_source: bool = True,
    ) -> str:
        """Answer a question using RAG.

        Args:
            question: User question.
            
        Returns:
            Answer.
        """
        config = {"configurable": {"thread_id": thread_id}}

        logger.info("Before self.agent.invoke")
        result = self.agent.invoke(
            {"messages": [{"role": "user", "content": question}]},
            config
        )
        logger.info("After self.agent.invoke")

        
        return {"answer": result["messages"][-1].content}

        '''
        # Step 1: Optionally filter sources using LLM
        metadata_filter = None
        selected_sources = []

        
        if filter_by_source:
            selected_sources = self._select_sources(question)
            if selected_sources:
                metadata_filter = {"app_name": {"$in": selected_sources}}
                logger.debug(f"Filtering by sources: {selected_sources}")
        

        # Step 2: Retrieve relevant documents
        docs = self.agent.invoke(
            query_text=question,
            n_results=self.top_k,
            threshold=self.threshold,
            #where=metadata_filter,
        )

        # Step 3: Handle no results
        if not docs:
            logger.info("No relevant documents found")
            return {
                "answer": "I couldn't find any relevant reviews to answer your question.",
                "sources": [],
                "num_docs": 0,
            }

        # Step 4: Format context
        context = self._format_context(docs)

        # Step 5: Generate answer
        answer = self._generate_answer(question, context)

        # Step 6: Extract unique sources
        sources = list({doc["metadata"].get("app_name", "unknown") for doc in docs})

        return {
            "answer": answer,
            "sources": sources,
            "num_docs": len(docs),
            "selected_sources": selected_sources,
        }
        '''
    '''
    def _select_sources(self, question: str) -> list[str]:
        """Use LLM to select relevant sources."""
        app_names = self.vector_store.get_all_metadata_values("app_name")

        if not app_names:
            return []

        prompt = PromptTemplate(
            template=SOURCE_SELECTION_PROMPT,
            input_variables=["sources", "query"],
        )

        formatted = prompt.format(
            sources=", ".join(sorted(app_names)),
            query=question,
        )

        response = self.llm.invoke_structured(formatted)
        
        # invoke_structured returns a list
        if not response or (isinstance(response, list) and len(response) == 1 and response[0].lower() == "none"):
            return []

        logger.debug(f"LLM selected sources: {response}")

        return response
    

    def _format_context(self, docs: list[dict[str, Any]]) -> str:
        """Format retrieved documents into context string."""
        formatted_docs = []
        for doc in docs:
            meta = doc["metadata"]
            app = meta.get("app_name", "Unknown")
            rating = meta.get("rating", "?")
            text = doc["text"]
            formatted_docs.append(f"[{app} - {rating}★]\n{text}")

        return "\n\n".join(formatted_docs)

    def _generate_answer(self, question: str, context: str) -> str:
        """Generate answer using LLM."""
        prompt = PromptTemplate(
            template=RAG_PROMPT,
            input_variables=["context", "question"],
        )

        formatted = prompt.format(context=context, question=question)
        return self.llm.invoke(formatted)
    '''