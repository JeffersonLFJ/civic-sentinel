import os
import logging
import asyncio
from pathlib import Path
from typing import List, Dict
from src.config import settings
from src.core.ocr_engine import ocr_engine
from src.core.database import db_manager

logger = logging.getLogger(__name__)

class LocalFolderIngestor:
    """
    Ingestor para processamento de arquivos locais em massa.
    Monitora a pasta data/ingest e processa novos arquivos.
    """
    
    def __init__(self):
        self.watch_path = settings.INGEST_DIR
        self.watch_path.mkdir(parents=True, exist_ok=True)
        
    async def scan_and_process(self) -> Dict:
        """
        Varre a pasta, identifica arquivos (PDF, imagens) e submete ao motor de OCR/Indexação.
        """
        files = list(self.watch_path.glob("*"))
        # Filtra extensões suportadas
        supported_exts = {'.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.txt'}
        files_to_process = [f for f in files if f.suffix.lower() in supported_exts]
        
        if not files_to_process:
            logger.info("Nenhum arquivo encontrado para ingestão local.")
            return {"processed": 0, "skipped": 0, "errors": 0}

        results = {"processed": 0, "skipped": 0, "errors": 0}
        
        for file_path in files_to_process:
            try:
                # 1. Verifica se já foi ingerido (Deduplicação simples por nome de arquivo para o MVP)
                # O save_document_record poderia ser verificado antes, mas vamos processar e deixar o banco lidar se necessário,
                # ou checar aqui se já existe um registro com este nome.
                
                logger.info(f"Processando arquivo local: {file_path.name}")
                
                # 2. OCR / Extração de Texto
                ocr_results = await ocr_engine.process_document(str(file_path), doc_type="auto")
                text = ocr_results.get("extracted_text", "")
                
                if not text.strip():
                    logger.warning(f"Nenhum texto extraído de {file_path.name}. Pulando.")
                    results["skipped"] += 1
                    continue
                
                # 3. Salva Registro no SQLite
                doc_data = {
                    "filename": file_path.name,
                    "source": "local_ingest",
                    "storage_path": str(file_path),
                    "text_content": text,
                    "ocr_method": ocr_results.get("ocr_method", "local"),
                }
                
                doc_id = await db_manager.save_document_record(doc_data)
                
                # 4. Indexação no ChromaDB
                metadata = {
                    "filename": file_path.name,
                    "source": "local_ingest",
                    "ingested_at": ocr_results.get("timestamp")
                }
                
                await db_manager.index_document_text(
                    doc_id=doc_id,
                    text=text,
                    metadata=metadata
                )
                
                logger.info(f"Ingestão local concluída com sucesso: {file_path.name}")
                results["processed"] += 1
                
                # Opcional: Mover arquivo para uma pasta 'processed' para evitar re-processamento
                # processed_root = self.watch_path / "processed"
                # processed_root.mkdir(exist_ok=True)
                # file_path.rename(processed_root / file_path.name)
                
            except Exception as e:
                logger.error(f"Erro ao processar {file_path.name}: {e}")
                results["errors"] += 1
                
        return results

local_ingestor = LocalFolderIngestor()
