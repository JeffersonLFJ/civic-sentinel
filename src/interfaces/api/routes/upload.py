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

async def process_document_task(file_location: str, filename: str, source: str, doc_type: str, sphere: str = Sphere.MUNICIPAL.value):
    """
    Função core de processamento compartilhada entre Upload manual e Scan Local.
    """
    processed_dir = settings.DATA_DIR / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = Path(file_location)
    
    try:
        # Decision Logic based on DocType
        ocr_result = {"extracted_text": "", "ocr_method": "unknown"}
        structured_chunks = None # Specific for Laws
        
        # --- 1. Auto-Dispatch & Extraction Logic ---
        
        # Determine Dispatcher and Archetype
        # We preserve the user's manual category for the SQL database to avoid breaking UI/Filters.
        # But we refine the 'doc_type' metadata for the LLM ONLY if the choice was 'lei'.
        
        final_meta_type = doc_type
        
        # A) LEGISLATION DISPATCH
        if doc_type in ["lei", "legislation"]:
            # Specific Kelsen sub-classification ONLY for 'lei' selection
            final_meta_type = DocType.LEI_ORDINARIA.value
            fname_lower = filename.lower()
            if "constituicao" in fname_lower:
                final_meta_type = DocType.CONSTITUICAO.value
            elif "complementar" in fname_lower:
                final_meta_type = DocType.LEI_COMPLEMENTAR.value
            elif "decreto" in fname_lower:
                final_meta_type = DocType.DECRETO.value
            elif "portaria" in fname_lower:
                final_meta_type = DocType.PORTARIA.value
            elif "resolucao" in fname_lower:
                final_meta_type = DocType.RESOLUCAO.value
            
            if fname_lower.endswith((".html", ".htm")):
                from src.ingestors.html_law import html_law_ingestor
                logger.info(f"⚖️ Ingestão (Lei HTML - {final_meta_type}): {filename}")
                result = await html_law_ingestor.process_file(str(file_path), filename)
                if result["status"] == "success":
                    ocr_result["extracted_text"] = result["full_text"]
                    ocr_result["ocr_method"] = "html_law_parser"
                    structured_chunks = result["chunks"]
                else:
                    ocr_result["extracted_text"] = file_path.read_text(errors="ignore")
            else:
                logger.info(f"⚖️ Ingestão (Lei PDF/OCR - {final_meta_type}): {filename}")
                ocr_result = await ocr_engine.process_document(str(file_path))

        # B) TABLE DISPATCH
        elif doc_type == "tabela":
            logger.info(f"📊 Ingestão (Tabela): {filename}")
            from src.utils.text_processing import text_splitter
            import csv
            rows = []
            if filename.lower().endswith(".csv"):
                 with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    reader = csv.reader(f)
                    rows = list(reader)
            elif filename.lower().endswith((".xlsx", ".xls")):
                 try:
                    import pandas as pd
                    df = pd.read_excel(file_path)
                    rows = [df.columns.tolist()] + df.values.tolist()
                 except Exception as e:
                    ocr_result["extracted_text"] = f"Erro Excel: {e}"
            
            if rows:
                table_chunks = text_splitter.split_table(rows, chunk_size=50)
                structured_chunks = []
                full_text_buffer = []
                for idx, chunk_text in enumerate(table_chunks):
                    structured_chunks.append({
                        "text": chunk_text,
                        "metadata": {
                            "chunk_type": "table_fragment",
                            "page_number": idx + 1,
                            "doc_type": doc_type # Keeps 'tabela'
                        }
                    })
                    full_text_buffer.append(chunk_text)
                ocr_result["extracted_text"] = "\n\n".join(full_text_buffer)
                ocr_result["ocr_method"] = "table_splitter_v1"
            else:
                ocr_result["extracted_text"] = "Tabela vazia ou erro de leitura."

        # C) DIARIO DISPATCH
        elif doc_type in ["diario", "diario_oficial"]:
            logger.info(f"🏛️ Ingestão (Diário Oficial): {filename}")
            ocr_result = await ocr_engine.process_document(str(file_path))

        # D) DENUNCIA DISPATCH
        elif doc_type == "denuncia":
            logger.info(f"📄 Ingestão (Denúncia): {filename}")
            ocr_result = await ocr_engine.process_document(str(file_path))

        # E) GENERAL DISPATCH (Default)
        else:
            logger.info(f"🔍 Ingestão (Geral): {filename}")
            ocr_result = await ocr_engine.process_document(str(file_path))
            
            # Healing Heuristic for PDFs
            text = ocr_result.get("extracted_text", "")
            if text:
                import re
                text = re.sub(r'(?<=[a-zA-Z0-9,])\n(?=[a-zà-ù])', ' ', text)
                ocr_result["extracted_text"] = text 
        
        # --- 2. Sphere Heuristics ---
        # Se a esfera for desconhecida, tentamos inferir pelo nome ou conteúdo.
        final_sphere = sphere
        content_sample = ocr_result["extracted_text"][:2000].lower()
        fname_lower = filename.lower()
        
        if final_sphere == Sphere.DESCONHECIDA.value:
            if any(k in fname_lower or k in content_sample for k in ["união", "brasil", "nacional", "federal", "ministério"]):
                final_sphere = Sphere.FEDERAL.value
            elif any(k in fname_lower or k in content_sample for k in ["estadual", "estado de", "rj", "governadoria"]):
                final_sphere = Sphere.ESTADUAL.value
            elif any(k in fname_lower or k in content_sample for k in ["prefeitura", "municipal", "município", "nova iguaçu", "semus"]):
                final_sphere = Sphere.MUNICIPAL.value

        # Persistence Logic
        storage_path = None
        if source in ["admin", "local_ingest"]:
            # Move ou copia para processed
            final_path = processed_dir / filename
            if str(file_path) != str(final_path):
                shutil.copy2(str(file_path), str(final_path))
            storage_path = str(final_path)
        
        # Save DB - WE KEEP THE ORIGINAL doc_type HERE
        from src.core.database import db_manager
        doc_data = {
            "filename": filename,
            "source": source,
            "storage_path": storage_path,
            "text_content": ocr_result["extracted_text"],
            "ocr_method": ocr_result["ocr_method"],
            "doc_type": doc_type, # PERSIST THE USER CHOICE
            "sphere": final_sphere,
            "status": "pending" # ALL uploads go to Quarentena
        }
        
        doc_id = await db_manager.save_document_record(doc_data)
        
        # --- 3. STAGING AREA BYPASS ---
        # We DO NOT index in ChromaDB yet. 
        # Vectorization only happens after Human Approval in Admin.
        
        logger.info(f"⏳ Documento {filename} enviado para QUARENTENA. ID: {doc_id}")
        return doc_id
        
    except Exception as e:
        logger.error(f"❌ Erro no processamento de {filename}: {e}")
        raise e

@router.post("/")
async def upload_document(
    file: UploadFile = File(...),
    source: str = Form("user"),
    doc_type: str = Form("generico"),
    sphere: str = Form(Sphere.MUNICIPAL.value)
):
    temp_dir = settings.DATA_DIR / "uploads_temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    file_location = temp_dir / file.filename
    
    try:
        logger.info(f"💾 Recebendo upload: {file.filename}")
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        doc_id = await process_document_task(str(file_location), file.filename, source, doc_type, sphere)
        
        # Cleanup temp
        if file_location.exists():
            os.remove(file_location)

        return {"status": "processed", "doc_id": doc_id}
        
    except Exception as e:
        if file_location.exists():
            os.remove(file_location)
        raise HTTPException(status_code=500, detail=str(e))
