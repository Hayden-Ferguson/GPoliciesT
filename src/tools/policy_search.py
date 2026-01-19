"""Prompt templates for RAG pipeline."""

from langchain.tools import tool
from typing import Optional
from src.services.vector_store import VectorStore

def build_policy_search_tool(
    vector_store: VectorStore
):
    @tool
    def university_policy_search(
        query: str,
        k: Optional[int] = 4
    ) -> list[dict]:
        """
        Search a database for university policies.

        Args:
        query: semantic search query
        k: max number of documents to retrieve
        """
        return vector_store.query(query_text=query, k=k)
        #return {"results": vector_store.query(query_text=query, k=k)}

    return university_policy_search
