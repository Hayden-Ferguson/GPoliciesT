import os
import time

#import boto3
import chromadb

from langchain.tools import tool

#from pydantic import BaseModel, Field
from typing import Optional

#import numpy as np
try:
    # Try modern import first
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    # Fallback to legacy import
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
    except ImportError:
        # Last resort
        from langchain.text_splitter import RecursiveCharacterTextSplitter

import uuid

from langchain.agents import create_agent
#from langchain.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langchain.chat_models import init_chat_model

from langgraph.checkpoint.postgres import PostgresSaver

from dotenv import load_dotenv


# ============================================================================
# Start
# ============================================================================


load_dotenv()

#Langsmith Credentials
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "postgres-agent-memory")

#Model ID
MODEL = os.getenv("MODEL", "anthropic.claude-3-sonnet-20240229-v1:0")
#BEDROCK_MODEL = "bedrock:anthropic.claude-3-5-sonnet-20241022-v2:0"

#Chromadb information
CHROMA_DATABASE = os.getenv("CHROMA_DATABASE", "dev-demo") # Usually 'default_database'
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "rag_collection")

try:
    chroma_client = chromadb.PersistentClient(path="./my_chroma_db")
    
    collection = chroma_client.get_or_create_collection(name=CHROMA_COLLECTION_NAME)
    print(f"   Connected to Chromadb collection: '{CHROMA_COLLECTION_NAME}'.")
    print(f"   Current Collection Count: {collection.count()}")
except Exception as e:
    print(f"   Error initializing ChromaDB Cloud: {e}")

SOURCE_DIR = "files"
CHUNKED_DIR = os.path.join(SOURCE_DIR, "chunked")

# Create chunked directory if it doesn't exist
if not os.path.exists(CHUNKED_DIR):
    os.makedirs(CHUNKED_DIR)
    print(f"Created directory: {CHUNKED_DIR}")
else:
    print(f"Directory exists: {CHUNKED_DIR}")

# List source files (excluding directory or hidden files)
source_files = [f for f in os.listdir(SOURCE_DIR) if os.path.isfile(os.path.join(SOURCE_DIR, f)) and not f.startswith('.')]
print(f"Found {len(source_files)} files in {SOURCE_DIR}: {source_files[:5]} ...")


# ============================================================================
# Chunking
# ============================================================================
def chunking():
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
            
            collection.add(
                documents=batch_docs,
                metadatas=batch_metas,
                ids=batch_ids
            )
            print(f"   ✅ Processed batch {i} to {min(i+BATCH_SIZE, total_docs)}")
            
        print(f"\nSuccessfully added all {total_docs} documents to ChromaDB!")
        print(f"Final Collection Count: {collection.count()}")
        
    except Exception as e:
        print(f"Error adding to ChromaDB: {e}")




@tool
def university_policy_search(
    query: str,
    k: Optional[int] = 4
) -> str:
    """
    Search a database for university policies.

    Args:
    query = query for semantic search
    k = max number of documents retrieved
    """

    results = collection.query(query_texts=[query], n_results=k)

    docs = ""
    
    # Check if we got results
    if results['documents'] and results['documents'][0]:
        # Iterate through the first query's results
        for text, meta, dist in zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        ):
            # Filter by threshold
            if dist <= 1.5:
                docs+= text

    return docs


# ============================================================================
# Testing
# ============================================================================

def test():
    model = init_chat_model(MODEL)
    print(f"  Model created: {type(model).__name__}")
    print(f"  Provider string: '{MODEL}'")
    
    tools = [university_policy_search]

    DB_URI = os.getenv(
        "DATABASE_URI",
        "postgresql://postgres2:postgres2@localhost:5433/postgres2"
    )

    agent = None

    #Postgres database memory
    with PostgresSaver.from_conn_string(
        DB_URI
    ) as checkpointer:

        checkpointer.setup()  

        agent = create_agent(
            model=model,
            tools=tools,
            system_prompt="You are a helpful assistant for searching through Richmond "
            "University policies. Be concise.",
            checkpointer=checkpointer,  # Memory
            name="policy_bot"
        )
    
        print("Agent created")

        #configuration for thread_id
        config = {"configurable": {"thread_id": "test_session"}}
        
        result = agent.invoke(
            {"messages": [("user", "What is the policy on drugs?")]},
            config
        )

        print(result["messages"][-1].content)
        
        result = agent.invoke(
            {"messages": [("user", "What question did I just ask?")]},
            config
        )

        print(result["messages"][-1].content)

        return model


# ============================================================================
# Main Function
# ============================================================================

if __name__ == "__main__":
    test()
