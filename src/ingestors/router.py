import logging
import asyncio
from typing import Dict, Any, Literal
from pathlib import Path

# Processors
from src.ingestors.docling_processor import docling_processor
from src.ingestors.law_scraper import LawScraper
from src.core.ocr_engine import ocr_engine # For Vision Fallback helper if needed

logger = logging.getLogger(__name__)

IngestionType = Literal["documento", "legislacao", "tabela", "diario"]

class IngestionRouter:
    """
    Roteador central que despacha o arquivo para o processador correto
    baseado na escolha explícita do usuário.
    """
    
    async def route(self, file_path: str, doc_type: IngestionType) -> Dict[str, Any]:
        logger.info(f"🔀 Roteando {Path(file_path).name} como [{doc_type}]")
        
        try:
            if doc_type == "legislacao":
                return await self._process_legislacao(file_path)
            
            elif doc_type == "tabela":
                return await self._process_tabela(file_path)
                
            elif doc_type == "diario":
                # Diario Oficial -> Docling (Markdown preserve structure better than raw text)
                return await docling_processor.process(file_path)
                
            else:
                # Default "documento" (PDFs, Imagens)
                return await self._process_documento(file_path)
                
        except Exception as e:
            logger.error(f"Erro no roteamento de ingestão: {e}")
            raise e

    async def _process_legislacao(self, file_path: str) -> Dict[str, Any]:
        # Se for HTML -> LawScraper (Limpeza + Chunking)
        # Se for PDF -> Docling (Layout Aware)
        
        path = Path(file_path)
        if path.suffix.lower() in [".html", ".htm"]:
            logger.info("Legislação HTML detectada. Usando LawScraper.")
            scraper = LawScraper()
            
            raw_html = ""
            try:
                # Try UTF-8 first
                with open(file_path, "r", encoding="utf-8") as f:
                    raw_html = f.read()
            except UnicodeDecodeError:
                logger.warning("Falha ao ler UTF-8. Tentando Latin-1 (comum em Planalto.gov).")
                try:
                    with open(file_path, "r", encoding="latin-1") as f:
                        raw_html = f.read()
                except Exception as e:
                    logger.error(f"Falha fatal de encoding: {e}")
                    # Last resort: ignore errors
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        raw_html = f.read()

            clean_text, chunks = scraper.parse_html_content(raw_html, path.name)
            return {
                "extracted_text": clean_text,
                "chunks": chunks, # Return structured chunks!
                "ocr_method": "law_scraper_html",
                "doc_type": "legislacao"
            }
        else:
            # PDF Lei -> Docling
            # Docling is great for layout, hopefully it keeps Articles intact.
            return await docling_processor.process(file_path)

    async def _process_tabela(self, file_path: str) -> Dict[str, Any]:
        # Estratégia Tabela Persistente
        # Por enquanto, lemos como texto e deixamos o TextSplitter.split_table lidar com isso?
        # O ideal seria converter XLS/CSV para Markdown Table aqui.
        
        path = Path(file_path)
        if path.suffix.lower() == ".csv":
            import pandas as pd
            try:
                df = pd.read_csv(file_path)
                # Convert to Markdown
                md = df.to_markdown(index=False)
                return {
                    "extracted_text": md,
                    "ocr_method": "pandas_markdown",
                    "doc_type": "tabela"
                }
            except Exception as e:
                logger.error(f"Falha ao ler CSV: {e}")
                # Fallback text
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    return {"extracted_text": f.read(), "ocr_method": "text_fallback"}
        
        elif path.suffix.lower() in [".xlsx", ".xls"]:
            import pandas as pd
            try:
                # Read first sheet
                df = pd.read_excel(file_path)
                md = df.to_markdown(index=False)
                return {
                    "extracted_text": md,
                    "ocr_method": "pandas_markdown_excel",
                    "doc_type": "tabela"
                }
            except Exception as e:
                logger.error(f"Falha ao ler Excel: {e}")
                return {"extracted_text": "", "ocr_method": "failed"}
                
        # Fallback
        return await docling_processor.process(file_path)

    async def _process_documento(self, file_path: str) -> Dict[str, Any]:
        # Docling principal
        result = await docling_processor.process(file_path)
        
        # Se Docling falhar ou retornar vazio (e for imagem), usar Vision Fallback
        if not result.get("extracted_text") or len(result.get("extracted_text", "")) < 50:
            # Check if it's an image
            if Path(file_path).suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
                logger.info("Texto insuficiente no Docling. Tentando Gemma Vision Fallback.")
                # Call OCR Engine for Vision logic (reusing existing code)
                vision_result = await ocr_engine.process_document(file_path, doc_type="foto_denuncia")
                return {
                    "extracted_text": vision_result.get("extracted_text"),
                    "ocr_method": vision_result.get("ocr_method"),
                    "doc_type": "foto_denuncia" # Auto-classificado como imagem
                }
                
        return result

ingestion_router = IngestionRouter()
