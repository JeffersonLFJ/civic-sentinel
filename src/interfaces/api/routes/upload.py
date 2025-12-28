from fastapi import APIRouter, UploadFile, File, HTTPException
from src.core.ocr_engine import ocr_engine
from src.config import settings
import shutil
import os
from pathlib import Path

router = APIRouter()

@router.post("/")
async def upload_document(
    file: UploadFile = File(...),
    source: str = "user" # "user" or "admin"
):
    """
    Uploads a document, processes OCR, and persists data based on source.
    - user: File is deleted, text is kept.
    - admin: File is kept, text is kept.
    """
    temp_dir = settings.DATA_DIR / "uploads_temp"
    processed_dir = settings.DATA_DIR / "processed"
    
    temp_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    file_location = temp_dir / file.filename
    
    try:
        # Save file tentatively
        import logging
        logger = logging.getLogger("src.interfaces.api.routes.upload")
        
        logger.info(f"💾 Salvando arquivo temporário: {file.filename}")
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Process with OCR
        logger.info(f"🔍 Iniciando extração de texto (OCR/PDF) para {file.filename}...")
        ocr_result = await ocr_engine.process_document(str(file_location))
        logger.info(f"✅ Texto extraído com sucesso ({ocr_result['ocr_method']}).")
        
        # Persistence Logic
        storage_path = None
        if source == "admin":
            final_path = processed_dir / file.filename
            logger.info(f"📂 Movendo arquivo para diretório processado: {final_path}")
            shutil.move(str(file_location), str(final_path))
            storage_path = str(final_path)
        else:
            # For user, we just delete the file after processing
            if file_location.exists():
                logger.info(f"🗑️ Removendo arquivo temporário (origem: user)")
                os.remove(file_location)
                
        # Save to DB (SQLite)
        logger.info("🗄️ Registrando metadados no SQLite...")
        from src.core.database import db_manager
        
        doc_data = {
            "filename": file.filename,
            "source": source,
            "storage_path": storage_path,
            "text_content": ocr_result["extracted_text"],
            "ocr_method": ocr_result["ocr_method"]
        }
        
        doc_id = await db_manager.save_document_record(doc_data)
        logger.info(f"📝 Registro salvo com ID: {doc_id}")
        
        # Save to Vector DB (Chroma)
        logger.info("🧠 Gerando fragmentos e indexando no banco vetorial (ChromaDB)...")
        await db_manager.index_document_text(
            doc_id=doc_id, 
            text=doc_data["text_content"],
            metadata={"source": source, "filename": file.filename}
        )
        logger.info("🎉 Indexação concluída com sucesso!")
        
        return {
            "status": "processed",
            "doc_id": doc_id,
            "filename": file.filename,
            "ocr_result": ocr_result,
            "persistence": "kept" if source == "admin" else "deleted"
        }
        
    except Exception as e:
        if file_location.exists():
            os.remove(file_location)
        raise HTTPException(status_code=500, detail=str(e))
