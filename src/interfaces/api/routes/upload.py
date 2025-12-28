from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from src.core.ocr_engine import ocr_engine
from src.config import settings
import shutil
import os
from pathlib import Path

router = APIRouter()

@router.post("/")
async def upload_document(
    file: UploadFile = File(...),
    source: str = Form("user"), # "user" or "admin"
    doc_type: str = Form("generico") # "lei", "denuncia", "generico", "diario"
):
    """
    Uploads a document with explicit type metadata.
    - lei (HTML): Uses structured parsing.
    - denuncia/generico: Uses OCR.
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
        
        logger.info(f"💾 Salvando arquivo ({doc_type}): {file.filename}")
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Decision Logic based on DocType
        ocr_result = {"extracted_text": "", "ocr_method": "unknown"}
        structured_chunks = None # Specific for Laws
        
        if doc_type == "lei" and file.filename.lower().endswith((".html", ".htm")):
            # Specialized HTML Law Ingestion
            from src.ingestors.html_law import html_law_ingestor
            logger.info("⚖️ Detectado Lei em HTML. Iniciando parsing estruturado...")
            
            result = await html_law_ingestor.process_file(str(file_location), file.filename)
            
            if result["status"] == "success":
                ocr_result["extracted_text"] = result["full_text"]
                ocr_result["ocr_method"] = "html_law_parse"
                structured_chunks = result["chunks"]
                logger.info(f"✅ Lei processada: {result['total_articles']} artigos identificados.")
            else:
                logger.error("Falha no parsing HTML. Tentando fallback texto simples.")
                ocr_result["extracted_text"] = Path(file_location).read_text(errors="ignore")
        
        elif doc_type == "tabela":
            # Spreadsheet Ingestion (Bypass OCR)
            logger.info("📊 Detectada Planilha/Tabela. Processando dados estruturados...")
            import csv
            
            extracted_text = ""
            if file.filename.lower().endswith(".csv"):
                with open(file_location, 'r', encoding='utf-8', errors='replace') as f:
                    reader = csv.reader(f)
                    rows = list(reader)
                    # Convert to Markdown Table for LLM readability
                    if rows:
                        header = "| " + " | ".join(rows[0]) + " |"
                        separator = "| " + " | ".join(["---"] * len(rows[0])) + " |"
                        body = "\n".join(["| " + " | ".join(row) + " |" for row in rows[1:]])
                        extracted_text = f"{header}\n{separator}\n{body}"
                    extract_method = "csv_direct"
            elif file.filename.lower().endswith((".xlsx", ".xls")):
                # Try pandas
                try:
                    import pandas as pd
                    df = pd.read_excel(file_location)
                    extracted_text = df.to_markdown(index=False)
                    extract_method = "excel_pandas"
                except ImportError:
                    extracted_text = "Erro: Pandas não instalado para processar Excel. Use CSV."
                    extract_method = "failed_excel"
                except Exception as e:
                    extracted_text = f"Erro ao ler Excel: {str(e)}"
                    extract_method = "failed_excel"
            else:
                extracted_text = "Formato não suportado para Tabela."
                extract_method = "invalid_format"
            
            ocr_result["extracted_text"] = extracted_text
            ocr_result["ocr_method"] = extract_method
            logger.info(f"✅ Tabela processada via {extract_method}.")

        else:
            # Standard Parsing (OCR or Text)
            logger.info(f"🔍 Iniciando extração padrão (OCR/PDF) para {file.filename}...")
            ocr_result = await ocr_engine.process_document(str(file_location))
            logger.info(f"✅ Texto extraído com sucesso ({ocr_result['ocr_method']}).")
        
        # Persistence Logic
        storage_path = None
        if source == "admin":
            final_path = processed_dir / file.filename
            shutil.move(str(file_location), str(final_path))
            storage_path = str(final_path)
        else:
            if file_location.exists():
                os.remove(file_location)
                
        # Save to DB (SQLite)
        logger.info("🗄️ Registrando metadados no SQLite...")
        from src.core.database import db_manager
        
        doc_data = {
            "filename": file.filename,
            "source": source,
            "storage_path": storage_path,
            "text_content": ocr_result["extracted_text"],
            "ocr_method": ocr_result["ocr_method"],
            "doc_type": doc_type
        }
        
        doc_id = await db_manager.save_document_record(doc_data)
        
        # Save to Vector DB (Chroma)
        logger.info("🧠 Indexando no banco vetorial (ChromaDB)...")
        
        if structured_chunks:
             # If we have perfect chunks from LawScraper, use them directly!
             # We need a new method in database.py or adapt index_document_text
             # For now, let's allow index_document_text to handle list of chunks if provided?
             # Or we call a new method. Let's add `index_structured_chunks` to db helper or hack existing.
             # Easiest: Call index_document_text but pass the pre-made chunks? No, that method splits.
             # Better: Add `index_pre_chunked_data` to database.py.
             await db_manager.index_pre_chunked_data(
                 doc_id=doc_id, 
                 chunks=structured_chunks, 
                 base_metadata={"source": source, "filename": file.filename, "doc_type": doc_type}
             )
        else:
            # Standard splitting
            await db_manager.index_document_text(
                doc_id=doc_id, 
                text=doc_data["text_content"],
                metadata={"source": source, "filename": file.filename, "doc_type": doc_type}
            )
            
        logger.info("🎉 Indexação concluída com sucesso!")
        
        return {
            "status": "processed",
            "doc_id": doc_id,
            "filename": file.filename,
            "method": ocr_result["ocr_method"]
        }
        
    except Exception as e:
        if file_location.exists():
            os.remove(file_location)
        logger.error(f"Erro critical upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))
