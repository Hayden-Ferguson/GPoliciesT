"""Ingestion service for text data."""

from pathlib import Path
from typing import Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
import pandas as pd

from src.services.vector_store import VectorStore
from src.config.logging import get_logger
import uuid
import os

logger = get_logger(__name__)


class IngestionService:
    """Handles ingestion of raw text data into a vector store."""

    def __init__(
        self, vector_store: VectorStore, chunk_size: int = 500, chunk_overlap: int = 100
    ):
        """Initialize with vector store and chunking config."""
        self.vector_store = vector_store
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def ingest_text(
        self,
        raw_text: str,
        metadata: dict[str, Any],
    ) -> int:
        """Ingests a single text document.

        Args:
            raw_text: The raw text document to ingest.
            metadata: Metadata for the document.

        Returns:
            Number of chunks added.
        """
        chunks = self.splitter.split_text(raw_text)
        metadatas = [
            {**metadata, "chunk_index": i, "total_chunks": len(chunks)}
            for i in range(len(chunks))
        ]

        return self.vector_store.add_documents(
            documents=chunks,
            metadatas=metadatas,
        )

    def batch_ingest_texts(
        self,
        raw_texts: list[str],
        metadatas: list[dict],
        ids: list[str] = None,
        batch_size: int = 500,
    ) -> int:
        """
        Batch ingests the provided list of texts using the provided list of metadatas

        Args:
            raw_texts: List of texts to chunk and ingest.
            metadata: Metadata for each text.
            batch_size: Amount to process per batch.
        Returns:
            Number of chunks added.
        """

        if len(raw_texts) != len(metadatas):
            raise ValueError("Length of raw_texts and metadatas must be the same.")

        if ids is not None and len(raw_texts) != len(ids):
            raise ValueError(
                "Length of raw_texts and ids must be the same when ids are provided."
            )

        total = 0  # total number of added documents (chunks)

        for i in range(0, len(raw_texts), batch_size):
            batch_chunks = []
            batch_metadatas = []
            batch_ids = [] if ids else None

            for j in range(i, min(i + batch_size, len(raw_texts))):
                chunks = self.splitter.split_text(raw_texts[j])

                for k, chunk in enumerate(chunks):
                    batch_chunks.append(chunk)
                    batch_metadatas.append(
                        {
                            **metadatas[j],
                            "chunk_index": k,
                            "total_chunks": len(chunks),
                        }
                    )
                    # Generate chunk ID if ids are provided
                    if ids is not None:
                        batch_ids.append(f"{ids[j]}_chunk_{k}")

            total += self.vector_store.add_documents(
                documents=batch_chunks,
                metadatas=batch_metadatas,
                ids=batch_ids,
            )

        return total

    def chunk(
        self,
        dir: Path,
        text_column: str = "enriched_text",
        id_column: str = "review_id",
        batch_size: int = 500,
        clear_existing: bool = False,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """Ingest a preprocessed txt file.

        Args:
            file_path: Path to a preprocessed CSV file.
            text_column: column name for the documents.
            id_column: column name for the ids.
            batch_size: Amount to process per batch.
            clear_existing: Whether to clear any existing collection.
            limit: Maximum number of rows to ingest.
        Returns:
            Dict with ingestion stats.
        """

        
        CHUNKED_DIR = os.path.join(dir, "chunked")

        chunked_files = [f for f in os.listdir(CHUNKED_DIR) if f.endswith('.txt')]

        documents = []
        metadatas = []
        ids = []

        print(f"Chunking {len(chunked_files)} files.")

        for file_name in chunked_files:
            file_path = os.path.join(CHUNKED_DIR, file_name)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Parse Metadata from Filename
                # Format: ch{index}-{original_name}-{len}.txt
                # Example: ch1-academic_policy-len495.txt
                try:
                    name_no_ext = os.path.splitext(file_name)[0]
                    parts = name_no_ext.split('-')
                    
                    # 1. Chunk Part (first item, e.g., 'ch1')
                    chunk_part = int(parts[0].replace('ch', ''))
                    
                    # 2. Size (last item, e.g., 'len495')
                    size = int(parts[-1].replace('len', ''))
                    
                    # 3. File Name (everything in between)
                    original_filename = "-".join(parts[1:-1])
                    
                    meta = {
                        "source": file_name,
                        "file_name": original_filename,
                        "chunk_part": chunk_part,
                        "size": size
                    }
                except Exception as e:
                    # Fallback if naming convention doesn't match
                    print(f"⚠️ Metadata parse warning for {file_name}: {e}")
                    meta = {"source": file_name}

                # Add to lists
                documents.append(content)
                metadatas.append(meta)
                ids.append(str(uuid.uuid4()))
                
            except Exception as e:
                print(f"Warning: Could not read {file_name}: {e}")

        print(f"Prepared {len(documents)} documents for embedding.")


        print("Upserting documents to ChromaDB Collection in batches...")

        BATCH_SIZE = 100  # Safe batch size
        total_docs = len(documents)

        try:
            for i in range(0, total_docs, BATCH_SIZE):
                batch_docs = documents[i : i + BATCH_SIZE]
                batch_metas = metadatas[i : i + BATCH_SIZE]
                batch_ids = ids[i : i + BATCH_SIZE]
                
                self.vector_store.add_documents(
                    documents=batch_docs,
                    metadatas=batch_metas,
                    ids=batch_ids
                )
                print(f"   ✅ Processed batch {i} to {min(i+BATCH_SIZE, total_docs)}")
                
            print(f"\nSuccessfully added all {total_docs} documents to ChromaDB!")
            print(f"Final Collection Count: {self.vector_store.count()}")
            
        except Exception as e:
            print(f"Error adding to ChromaDB: {e}")

    def get_stats(self) -> dict[str, Any]:
        """Get current ingestion stats.

        Returns:
            Dict with collection stats.
        """
        count = self.vector_store.count()
        categories = self.vector_store.get_all_metadata_values("category")
        apps = self.vector_store.get_all_metadata_values("app_name")

        return {
            "total_documents": count,
            "unique_categories": len(categories),
            "unique_apps": len(apps),
            "categories": (
                sorted(categories)
                if len(categories) <= 20
                else f"{len(categories)} categories"
            ),
        }
