"""Ingest routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from pathlib import Path
import shutil
import tempfile

from src.config.logging import get_logger
from src.config.settings import Settings, get_settings
from src.dependencies import get_ingest_service
from src.services.ingest import IngestionService
from chromadb.errors import ChromaError

logger = get_logger(__name__)

router = APIRouter(prefix="/ingest", tags=["ingest"])

# Allowed filenames (or load dynamically)
ALLOWED_EXTENSIONS = {".csv"}


def _validate_filename(filename: str) -> Path:
    """Validate filename and return full path.
    
    Args:
        filename: Simple filename (no path separators).
        
    Returns:
        Full path to file in processed data directory.
        
    Raises:
        HTTPException: If filename is invalid or file doesn't exist.
    """
    settings = get_settings()
    
    # Block path traversal
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(
            status_code=400,
            detail="Invalid filename. Path separators not allowed.",
        )
    
    # Check extension
    if Path(filename).suffix.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {ALLOWED_EXTENSIONS}",
        )
    
    # Build path (always from processed directory)
    file_path = settings.processed_data_dir / filename
    
    # Verify file exists
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {filename}",
        )
    
    # Verify it's actually inside the data directory (extra safety)
    try:
        file_path.resolve().relative_to(settings.data_dir.resolve())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid file path.",
        )
    
    return file_path


@router.get("/files")
def list_available_files(
    settings: Settings = Depends(get_settings),
) -> dict:
    """List available CSV files for ingestion."""
    processed_dir = settings.processed_data_dir
    
    if not processed_dir.exists():
        return {"files": []}
    
    files = [
        f.name for f in processed_dir.iterdir()
        if f.is_file() and f.suffix.lower() in ALLOWED_EXTENSIONS
    ]
    
    return {"files": sorted(files)}

'''
@router.post("")
def ingest_csv(
    filename: str = Query(
        ...,
        description="CSV filename (must exist in processed data directory)",
        examples=["sentio_plus_rag_ready.csv"],
    ),
    clear_existing: bool = Query(
        default=False,
        description="Clear existing documents before ingesting",
    ),
    batch_size: int = Query(
        default=500,
        ge=1,
        le=5000,
        description="Documents per batch",
    ),
    limit: int | None = Query(
        default=None,
        ge=1,
        description="Max rows to ingest (None = all)",
    ),
    ingest_service: IngestionService = Depends(get_ingest_service),
) -> dict:
    """Ingest a CSV file into the vector store."""
    file_path = _validate_filename(filename)
    logger.info(f"Ingest request: {file_path.name}")

    try:
        result = ingest_service.ingest_csv(
            file_path=file_path,
            batch_size=batch_size,
            clear_existing=clear_existing,
            limit=limit,
        )
        return {"success": True, **result}
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
'''

'''@router.post("/upload")
async def upload_and_ingest(
    file: UploadFile = File(..., description="Folder to ingest"),
    clear_existing: bool = Query(default=False),
    batch_size: int = Query(default=500, ge=1, le=5000),
    limit: int | None = Query(default=None, ge=1),
    settings: Settings = Depends(get_settings),
    ingest_service: IngestionService = Depends(get_ingest_service),
) -> dict:
    """Upload and ingest a txt file."""
    contents = file.read()
    text = contents.decode("utf-8")

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

    ingest_service.ingest_text(contents)'''


@router.get("/stats")
def get_stats(
    ingest_service: IngestionService = Depends(get_ingest_service),
) -> dict:
    """Get ingestion statistics."""
    return ingest_service.get_stats()


@router.delete("")
def clear_collection(
    ingest_service: IngestionService = Depends(get_ingest_service),
) -> dict:
    """Clear all documents from the collection."""
    logger.info("Clear collection request")
    ingest_service.vector_store.clear()
    return {"success": True, "message": "Collection cleared"}