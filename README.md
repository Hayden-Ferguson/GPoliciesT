# GPoliciesT

A Retrieval-Augmented Generation (RAG) chatbot designed to help users understand and navigate the University of Richmond's policy database through natural language conversations.

## Overview

GPoliciesT combines advanced language models with vector search to provide accurate, context-aware answers about university policies. The system uses ChromaDB for efficient document retrieval, AWS Bedrock for language generation, and PostgreSQL for persistent conversation memory.

## Features

- **Intelligent Policy Search**: Vector-based semantic search across policy documents
- **Conversational Memory**: Thread-based conversation history stored in PostgreSQL
- **Multi-Model Support**: Compatible with AWS Bedrock (Claude) and OpenAI models
- **Document Ingestion**: CSV file processing and vectorization
- **Modern UI**: React-based chat interface with TailwindCSS and shadcn/ui components
- **RESTful API**: FastAPI backend with automatic OpenAPI documentation
- **Containerized Deployment**: Full Docker Compose setup for easy deployment

## Architecture

```
┌─────────────────┐
│   React UI      │  (Port 5173)
│   (Vite + TS)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   FastAPI       │  (Port 8000)
│   Backend       │
└────┬────────────┘
     │
     ├──────────────┐
     │              │
     ▼              ▼
┌─────────┐   ┌──────────┐
│ ChromaDB│   │PostgreSQL│
│ (Vector)│   │(Memory)  │
└─────────┘   └──────────┘
```

## Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **LangChain**: LLM orchestration and RAG pipeline
- **LangGraph**: Agent workflow management with checkpointing
- **ChromaDB**: Vector database for document embeddings
- **PostgreSQL**: Conversation memory persistence
- **AWS Bedrock**: Claude language models
- **OpenAI**: Alternative LLM provider

### Frontend
- **React 19**: UI framework
- **TypeScript**: Type-safe development
- **Vite**: Fast build tool
- **TailwindCSS**: Utility-first styling
- **shadcn/ui**: Component library
- **@assistant-ui/react**: Chat interface components
- **Zustand**: State management

### Infrastructure
- **Docker & Docker Compose**: Containerization
- **uvicorn**: ASGI server

## Prerequisites

- Docker and Docker Compose
- AWS Account (for Bedrock access) or OpenAI API key
- LangSmith account (optional, for tracing)

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Hayden-Ferguson/GPoliciesT.git
cd GPoliciesT
```

### 2. Configure Environment Variables

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` and provide:

- **AWS Credentials**: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`
- **OpenAI API Key**: `OPENAI_API_KEY` (if using OpenAI)
- **LangSmith**: `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT` (optional)
- **Model Selection**: Choose between Bedrock Claude models or OpenAI
- **Database**: PostgreSQL credentials (defaults provided)
- **ChromaDB**: Configuration for vector store

### 3. Start the Application

```bash
docker compose up
```

This will start four services:
- **chromadb**: Vector database (port 8001)
- **postgres**: Conversation memory (port 5433)
- **api**: FastAPI backend (port 8000)
- **my-app**: React frontend (port 5173)

### 4. Access the Application

- **Frontend**: http://localhost:5173
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Query Endpoints

- `POST /query` - Submit a question to the RAG system
  ```json
  {
    "question": "What is the academic honesty policy?",
    "thread_id": "thread_abc123"
  }
  ```

- `POST /query/threads` - Create a new conversation thread

### Ingestion Endpoints

- `GET /ingest/stats` - Get document ingestion statistics

### System Endpoints

- `GET /` - API information
- `GET /health` - Health check with document count

## Project Structure

```
GPoliciesT/
├── src/                      # Backend source code
│   ├── main.py              # FastAPI application entry point
│   ├── config/              # Configuration and settings
│   ├── routes/              # API route handlers
│   │   ├── query.py         # Query endpoints
│   │   └── ingest.py        # Ingestion endpoints
│   ├── services/            # Business logic
│   │   ├── agent.py         # LangGraph agent service
│   │   ├── llm.py           # LLM client wrapper
│   │   ├── vector_store.py  # ChromaDB integration
│   │   └── ingest.py        # Document processing
│   └── schemas/             # Pydantic models
├── my-app/                  # Frontend React application
│   ├── src/
│   │   ├── App.tsx          # Main application component
│   │   └── components/      # React components
│   └── package.json
├── data/                    # Data directory for documents
├── files/                   # Policy files storage
├── my_chroma_db/           # ChromaDB persistence
├── docker-compose.yml      # Container orchestration
├── Dockerfile              # Backend container image
├── pyproject.toml          # Python dependencies
└── .env                    # Environment configuration
```

## Development

### Running Locally (Without Docker)

**Backend:**
```bash
# Install dependencies
pip install uv
uv pip install .

# Start ChromaDB and PostgreSQL separately
# Then run the API
uvicorn src.main:app --reload --port 8000
```

**Frontend:**
```bash
cd my-app
npm install
npm run dev
```

### Adding Documents

Place CSV files in the `data/processed/` directory and use the ingestion API to process them into the vector database.

## Configuration

Key configuration options in `.env`:

- `MODEL`: Choose your LLM (e.g., `anthropic.claude-3-5-sonnet-20241022-v2:0`)
- `CHROMA_CLIENT_TYPE`: `http` (for Docker) or `persistent` (local)
- `CHECKPOINT_TYPE`: `postgres` (persistent) or `memory` (ephemeral)
- `DATABASE_URI`: PostgreSQL connection string

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

## Support

For issues or questions, please open an issue on GitHub.
