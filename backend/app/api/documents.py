from fastapi import APIRouter, HTTPException
from loguru import logger
from app.services.vector_store import get_collection_stats, delete_documents

router = APIRouter()

@router.get("/documents")
async def list_documents():
    """Return stats about what's stored in ChromaDB."""
    stats = await get_collection_stats()
    return stats

@router.delete("/documents/{file_id}")
async def delete_document(file_id: str):
    """Delete all chunks for a given file_id."""
    try:
        deleted = await delete_documents(file_id)
        return {"deleted_chunks": deleted, "file_id": file_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))