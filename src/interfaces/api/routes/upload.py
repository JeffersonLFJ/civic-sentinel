from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from src.core.ocr_engine import ocr_engine
from src.config import settings
import shutil
import os
from pathlib import Path
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("src.interfaces.api.routes.upload")
router = APIRouter()

async def process_document_task(file_location: str, filename: str, source: str, doc_type: str):
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
        
        # --- 1. Extração Inicial (A "bagunçada") ---
        if doc_type == "lei" and filename.lower().endswith((".html", ".htm")):
            from src.ingestors.html_law import html_law_ingestor
            logger.info(f"⚖️ Ingestão: {filename} detectado como Lei.")
            result = await html_law_ingestor.process_file(str(file_path), filename)
            
            if result["status"] == "success":
                ocr_result["extracted_text"] = result["full_text"]
                ocr_result["ocr_method"] = "html_law_parser"
                structured_chunks = result["chunks"]
            else:
                ocr_result["extracted_text"] = file_path.read_text(errors="ignore")
        
        elif doc_type == "tabela":
            logger.info(f"📊 Ingestão: {filename} detectado como Tabela.")
            import csv
            extracted_text = ""
            extract_method = "unknown" # Initialize extract_method
            if filename.lower().endswith(".csv"):
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    reader = csv.reader(f)
                    rows = list(reader)
                    if rows:
                        header = "| " + " | ".join(rows[0]) + " |"
                        separator = "| " + " | ".join(["---"] * len(rows[0])) + " |"
                        body = "\n".join(["| " + " | ".join(row) + " |" for row in rows[1:]])
                        extracted_text = f"{header}\n{separator}\n{body}"
                    extract_method = "csv_direct"
            elif filename.lower().endswith((".xlsx", ".xls")):
                try:
                    import pandas as pd
                    df = pd.read_excel(file_path)
                    extracted_text = df.to_markdown(index=False)
                    extract_method = "excel_pandas"
                except Exception as e:
                    extracted_text = f"Erro Excel: {e}"
                    extract_method = "failed_excel"
            
            ocr_result["extracted_text"] = extracted_text
            ocr_result["ocr_method"] = extract_method

        else:
            logger.info(f"🔍 Ingestão: {filename} processamento padrão (OCR/PDF).")
            ocr_result = await ocr_engine.process_document(str(file_path))
            
            # --- 2. Análise Semântica / Refinamento (A "distinção melhor") ---
            text = ocr_result.get("extracted_text", "")
            
            if text and not structured_chunks:
                import re
                # A) Heurística de Correção de Quebra de Linha (PDFs "quebrados")
                # Ex: "sis\ntema" -> "sistema" (se não houver ponto antes)
                logger.info("Mecanismo de 'Healing': Corrigindo quebras de linha artificiais...")
                # Remove \n se precedido de letra e seguido de letra minúscula (continuidade)
                text = re.sub(r'(?<=[a-zA-Z0-9,])\n(?=[a-zà-ù])', ' ', text)
                ocr_result["extracted_text"] = text

                # B) Detecção de Lei em PDF
                law_patterns = len(re.findall(r'(?:^|\n)\s*Art\.\s*\d+', text, re.IGNORECASE))
                if law_patterns > 5:
                    logger.info("⚖️ Detectada estrutura de LEI dentro do PDF (Hybrid Chunking).")
                    doc_type = "lei" # Força o splitter de lei no indexador

        
        # Persistence Logic
        storage_path = None
        if source == "admin" or source == "local_ingest":
            # Se for admin, movemos para processed. 
            # Se for local_ingest, COPIAMOS (ou movemos se preferir, manteremos compatibilidade com admin)
            final_path = processed_dir / filename
            if str(file_path) != str(final_path):
                shutil.copy2(str(file_path), str(final_path))
            storage_path = str(final_path)
        
        # Save DB
        from src.core.database import db_manager
        doc_data = {
            "filename": filename,
            "source": source,
            "storage_path": storage_path,
            "text_content": ocr_result["extracted_text"],
            "ocr_method": ocr_result["ocr_method"],
            "doc_type": doc_type
        }
        
        doc_id = await db_manager.save_document_record(doc_data)
        
        # Index Chroma
        if structured_chunks:
            await db_manager.index_pre_chunked_data(
                doc_id=doc_id, 
                chunks=structured_chunks, 
                base_metadata={"source": source, "filename": filename, "doc_type": doc_type}
            )
        else:
            await db_manager.index_document_text(
                doc_id=doc_id, 
                text=doc_data["text_content"],
                metadata={"source": source, "filename": filename, "doc_type": doc_type}
            )
            
        logger.info(f"🎉 Indexação concluída com sucesso! ID: {doc_id}")
        return doc_id
        
    except Exception as e:
        logger.error(f"❌ Erro no processamento de {filename}: {e}")
        raise e

@router.post("/")
async def upload_document(
    file: UploadFile = File(...),
    source: str = Form("user"),
    doc_type: str = Form("generico")
):
    temp_dir = settings.DATA_DIR / "uploads_temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    file_location = temp_dir / file.filename
    
    try:
        logger.info(f"💾 Recebendo upload: {file.filename}")
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        doc_id = await process_document_task(str(file_location), file.filename, source, doc_type)
        
        # Cleanup temp
        if source != "admin": # Admin logic moves it in task or copies
             if file_location.exists(): os.remove(file_location)
        else:
             if file_location.exists(): os.remove(file_location) # Já copiado para processed

        return {"status": "processed", "doc_id": doc_id}
        
    except Exception as e:
        if file_location.exists(): os.remove(file_location)
        raise HTTPException(status_code=500, detail=str(e))
