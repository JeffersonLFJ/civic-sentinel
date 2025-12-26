from fastapi import APIRouter, HTTPException, Query
from src.core.database import db_manager
from typing import List, Dict, Any

router = APIRouter()

@router.get("/", response_model=List[Dict[str, Any]])
async def list_documents(limit: int = 50, offset: int = 0):
    """
    List ingested documents with metadata.
    """
    try:
        docs = await db_manager.get_all_documents(limit, offset)
        return docs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    """
    Delete a document and its vectors.
    """
    try:
        success = await db_manager.delete_document(doc_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"status": "deleted", "id": doc_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
