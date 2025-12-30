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
        
    async def list_pending_files(self) -> List[Dict]:
        """
        Lista arquivos na pasta de ingestão e sugere um tipo baseado na extensão.
        """
        files = list(self.watch_path.glob("*"))
        supported_exts = {'.pdf', '.png', '.jpg', '.jpeg', '.txt', '.html', '.xlsx', '.csv'}
        pending = []
        
        for f in files:
            if f.suffix.lower() in supported_exts:
                # Sugestão básica de tipo
                ext = f.suffix.lower()
                suggested_type = "denuncia" # Default (PDF/Imagens)
                if ext == ".html": suggested_type = "lei"
                elif ext in {".xlsx", ".csv"}: suggested_type = "tabela"
                elif "diario" in f.name.lower(): suggested_type = "diario"
                
                pending.append({
                    "filename": f.name,
                    "size": f.stat().st_size,
                    "suggested_type": suggested_type,
                    "path": str(f)
                })
        return pending

    async def process_selected_files(self, items: List[Dict]) -> Dict:
        """
        Processa uma lista de arquivos com seus respectivos tipos definidos pelo usuário.
        item: {"filename": "doc.pdf", "doc_type": "lei"}
        """
        results = {"processed": 0, "skipped": 0, "errors": 0}
        
        for item in items:
            filename = item["filename"]
            doc_type = item["doc_type"]
            file_path = self.watch_path / filename
            
            if not file_path.exists():
                logger.error(f"Arquivo não encontrado para processamento: {filename}")
                results["errors"] += 1
                continue
                
            try:
                logger.info(f"🚀 Ingestão Local: Processando {filename} como {doc_type}")
                
                # Reutilizamos a lógica de upload para manter consistência
                from src.interfaces.api.routes.upload import process_document_task
                from src.core.constants import Sphere
                
                # Se o usuário não enviou a esfera, manda 'unknown' para disparar as heurísticas automáticas
                sphere = item.get("sphere", Sphere.DESCONHECIDA.value)
                
                await process_document_task(str(file_path), filename, "local_ingest", doc_type, sphere)
                
                results["processed"] += 1
                
            except Exception as e:
                logger.error(f"Erro ao processar localmente {filename}: {e}")
                results["errors"] += 1
                
        return results

local_ingestor = LocalFolderIngestor()
