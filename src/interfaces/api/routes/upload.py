from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from src.core.ocr_engine import ocr_engine
from src.config import settings
from src.core.constants import DocType, Sphere
import shutil
import os
import hashlib
import re
from pathlib import Path
import logging
from typing import Dict, Any, List, Optional
from src.utils.security import sanitize_filename

logger = logging.getLogger("src.interfaces.api.routes.upload")
router = APIRouter()

from src.ingestors.router import ingestion_router, IngestionType

# --- Feature 1: DocType Heuristic Detection ---
LEGISLATION_PATTERNS = re.compile(
    r'(?:Art\.\s*\d|CAPÍTULO|TÍTULO\s+[IVX]|DECRETO\s+N[º°]|'
    r'LEI\s+N[º°]|LEI\s+COMPLEMENTAR|SEÇÃO\s+[IVX]|'
    r'DISPOSIÇÕES\s+TRANSITÓRIAS|Parágrafo\s+único)',
    re.IGNORECASE
)

def detect_doc_type_heuristic(text: str, filename: str) -> Optional[str]:
    """
    Analyzes the first 1000 chars and filename for legislation patterns.
    Returns suggested doc_type or None if no strong signal.
    """
    sample = text[:1000] if text else ""
    fname_lower = filename.lower()
    
    # Filename-based detection
    if any(kw in fname_lower for kw in ["lei ", "decreto ", "constituiç", "estatuto ", "lei_"]):
        return "legislacao"
    
    # Content-based detection
    matches = LEGISLATION_PATTERNS.findall(sample)
    if len(matches) >= 2:  # At least 2 patterns = strong signal
        return "legislacao"
    
    if "diário oficial" in sample.lower() or "diario oficial" in fname_lower:
        return "diario"
    
    return None


# --- Feature 4: Extraction Quality Classification ---
def classify_extraction_quality(ocr_method: str, text: str, file_path: str) -> str:
    """
    Classifies extraction quality based on method used and text density.
    Returns: 'high', 'medium', 'low', 'ocr_fallback'
    """
    if not text or len(text) < 50:
        return "low"
    
    if ocr_method in ["law_scraper_html", "pandas_markdown", "pandas_markdown_excel"]:
        return "high"  # Structured extraction
    
    if ocr_method and "tesseract" in ocr_method.lower():
        return "ocr_fallback"
    
    if ocr_method and "vision" in ocr_method.lower():
        return "medium"  # Better than Tesseract but still OCR
    
    # For Docling/router_default: check text density per page
    try:
        from PyPDF2 import PdfReader
        if file_path.lower().endswith('.pdf'):
            reader = PdfReader(file_path)
            num_pages = len(reader.pages)
            if num_pages > 0:
                chars_per_page = len(text) / num_pages
                if chars_per_page < 100:  # Density metric
                    return "low"  # Likely scanned/xerocado
                elif chars_per_page < 500:
                    return "medium"
    except Exception:
        pass  # PyPDF2 not available or not a PDF
    
    return "high"  # Docling with good text = high quality


async def process_document_task(file_location: str, filename: str, source: str, doc_type: str = "documento", sphere: str = "unknown", tags: str = ""):
    """
    Função core de processamento usando o novo IngestionRouter.
    """
    processed_dir = settings.DATA_DIR / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = Path(file_location)
    
    try:
        logger.info(f"🔄 Inicia ingestão via Router: {filename} [{doc_type}]")
        
        # --- Feature 2: SHA-256 Dedup ---
        file_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
        
        from src.core.database import db_manager
        if not db_manager._sqlite_connection:
            await db_manager.get_sqlite()
        
        async with db_manager._sqlite_connection.execute(
            "SELECT id, filename FROM documents WHERE file_hash = ?", (file_hash,)
        ) as cursor:
            existing = await cursor.fetchone()
        
        if existing:
            logger.warning(f"⚠️ Arquivo duplicado detectado! Hash {file_hash[:12]}... já existe como '{existing[1]}' (ID: {existing[0]})")
            raise HTTPException(
                status_code=409,
                detail=f"Este arquivo já foi enviado anteriormente como '{existing[1]}'. Duplicatas não são permitidas."
            )
        
        # Dispatch to Router
        valid_types = ["documento", "legislacao", "tabela", "diario"]
        safe_type = doc_type if doc_type in valid_types else "documento"
        
        ingestion_result = await ingestion_router.route(str(file_path), safe_type)
        
        extracted_text = ingestion_result.get("extracted_text", "")
        ocr_method = ingestion_result.get("ocr_method", "router_default")
        
        # --- Feature 1: DocType Heuristic ---
        suggested_type = detect_doc_type_heuristic(extracted_text, filename)
        if suggested_type and suggested_type != safe_type:
            logger.warning(f"⚠️ Heurística detectou tipo '{suggested_type}' mas usuário escolheu '{safe_type}'. Registrando sugestão.")
        
        # --- Feature 4: Extraction Quality ---
        extraction_quality = classify_extraction_quality(ocr_method, extracted_text, str(file_path))
        if extraction_quality in ["low", "ocr_fallback"]:
            logger.warning(f"⚠️ Qualidade de extração: {extraction_quality} para {filename}")
        
        # Persistence Logic
        storage_path = None
        if source in ["admin", "local_ingest", "user_upload"]:
            final_path = processed_dir / filename
            if str(file_path) != str(final_path):
                shutil.copy2(str(file_path), str(final_path))
            storage_path = str(final_path)
        
        doc_data = {
            "filename": filename,
            "source": source,
            "storage_path": storage_path,
            "text_content": extracted_text,
            "ocr_method": ocr_method,
            "doc_type": safe_type,
            "sphere": sphere,
            "status": "pending",
            "custom_tags": tags,
            "initial_chunks": ingestion_result.get("chunks", None),
            "file_hash": file_hash,
            "extraction_quality": extraction_quality,
            "suggested_doc_type": suggested_type,
        }
        
        doc_id = await db_manager.save_document_record(doc_data)
        
        logger.info(f"✅ Ingestão completa via Router. ID: {doc_id} | Quality: {extraction_quality} | Hash: {file_hash[:12]}...")
        return doc_id, suggested_type
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions (dedup)
    except Exception as e:
        logger.error(f"❌ Erro no processamento de {filename}: {e}")
        raise e

@router.post("/")
async def upload_document(
    file: UploadFile = File(...),
    source: str = Form("user"),
    tags: str = Form(""),
    doc_type: str = Form("documento"),
    custom_filename: Optional[str] = Form(None)
):
    temp_dir = settings.DATA_DIR / "uploads_temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    safe_upload_name = sanitize_filename(file.filename or "")
    if not safe_upload_name:
        raise HTTPException(status_code=400, detail="Invalid filename.")
    file_location = temp_dir / safe_upload_name
    
    try:
        # Validate MIME type
        allowed_mime = settings.allowed_upload_mime()
        allowed_exts = {".pdf", ".txt", ".html"}
        file_ext = Path(safe_upload_name).suffix.lower()
        if file.content_type not in allowed_mime and file_ext not in allowed_exts:
            raise HTTPException(status_code=415, detail="Unsupported file type.")

        # Validate size
        max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
        file.file.seek(0, os.SEEK_END)
        size = file.file.tell()
        file.file.seek(0)
        if size > max_bytes:
            raise HTTPException(status_code=413, detail="File too large.")

        logger.info(f"💾 Upload recebido: {file.filename} ({doc_type})")
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        raw_final_name = custom_filename if custom_filename and custom_filename.strip() else file.filename
        final_name = sanitize_filename(raw_final_name or "")
        if not final_name:
            raise HTTPException(status_code=400, detail="Invalid final filename.")
        
        doc_id, suggested_type = await process_document_task(
            str(file_location), 
            final_name, 
            source, 
            doc_type=doc_type, 
            sphere="unknown",
            tags=tags
        )
        
        if file_location.exists():
            os.remove(file_location)

        response = {"status": "processed", "doc_id": doc_id}
        
        # Feature 1: Include heuristic suggestion in response
        if suggested_type and suggested_type != doc_type:
            response["suggested_doc_type"] = suggested_type
            response["warning"] = f"O sistema detectou padrões de '{suggested_type}' neste documento. Considere reclassificar na quarentena."
        
        return response
        
    except HTTPException:
        if file_location.exists():
            os.remove(file_location)
        raise
    except Exception as e:
        if file_location.exists():
            os.remove(file_location)
        raise HTTPException(status_code=500, detail=str(e))
