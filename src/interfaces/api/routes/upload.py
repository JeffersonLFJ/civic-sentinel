from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from src.core.ocr_engine import ocr_engine
from src.config import settings
from src.core.constants import DocType, Sphere
import shutil
import os
from pathlib import Path
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("src.interfaces.api.routes.upload")
router = APIRouter()

from src.ingestors.router import ingestion_router, IngestionType

async def process_document_task(file_location: str, filename: str, source: str, doc_type: str = "documento", sphere: str = "unknown", tags: str = ""):
    """
    Função core de processamento usando o novo IngestionRouter.
    """
    processed_dir = settings.DATA_DIR / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = Path(file_location)
    
    try:
        logger.info(f"🔄 Inicia ingestão via Router: {filename} [{doc_type}]")
        
        # Dispatch to Router
        # doc_type string to IngestionType literal
        valid_types = ["documento", "legislacao", "tabela", "diario"]
        safe_type = doc_type if doc_type in valid_types else "documento"
        
        ingestion_result = await ingestion_router.route(str(file_path), safe_type)
        
        # Persistence Logic
        storage_path = None
        if source in ["admin", "local_ingest", "user_upload"]:
            final_path = processed_dir / filename
            if str(file_path) != str(final_path):
                shutil.copy2(str(file_path), str(final_path))
            storage_path = str(final_path)
        
        # Save DB
        from src.core.database import db_manager
        
        # Determine status: "pending" (Quarantine)
        # We classify as 'doc_type' but status is pending review.
        # Ideally, if user explicitly says "Legislation", maybe we can auto-approve?
        # Requirement: "Quarantine first". So status is pending.
        
        doc_data = {
            "filename": filename,
            "source": source,
            "storage_path": storage_path,
            "text_content": ingestion_result.get("extracted_text", ""),
            "ocr_method": ingestion_result.get("ocr_method", "router_default"),
            "doc_type": safe_type, # We trust the user's initial classification or Router's output
            "sphere": sphere,
            "status": "pending",
            "custom_tags": tags,
            "initial_chunks": ingestion_result.get("chunks", None) # Save initial chunks if available
        }
        
        doc_id = await db_manager.save_document_record(doc_data)
        
        logger.info(f"✅ Ingestão completa via Router. ID: {doc_id}")
        return doc_id
        
    except Exception as e:
        logger.error(f"❌ Erro no processamento de {filename}: {e}")
        raise e

@router.post("/")
async def upload_document(
    file: UploadFile = File(...),
    source: str = Form("user"),
    tags: str = Form(""),
    doc_type: str = Form("documento"), # New field
    custom_filename: Optional[str] = Form(None)
):
    temp_dir = settings.DATA_DIR / "uploads_temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    file_location = temp_dir / file.filename
    
    try:
        logger.info(f"💾 Upload recebido: {file.filename} ({doc_type})")
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        final_name = custom_filename if custom_filename and custom_filename.strip() else file.filename
        
        doc_id = await process_document_task(
            str(file_location), 
            final_name, 
            source, 
            doc_type=doc_type, 
            sphere="unknown",
            tags=tags
        )
        
        if file_location.exists():
            os.remove(file_location)

        return {"status": "processed", "doc_id": doc_id}
        
    except Exception as e:
        if file_location.exists():
            os.remove(file_location)
        raise HTTPException(status_code=500, detail=str(e))
