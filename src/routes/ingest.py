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

@router.get("/stats")
def get_stats(
    ingest_service: IngestionService = Depends(get_ingest_service),
) -> dict:
    """Get ingestion statistics."""
    return ingest_service.get_stats()