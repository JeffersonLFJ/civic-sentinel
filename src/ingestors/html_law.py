import logging
from pathlib import Path
from typing import Dict, Any, List
from src.ingestors.law_scraper import LawScraper

logger = logging.getLogger(__name__)

class HtmlLawIngestor:
    """
    Ingestor dedicado para arquivos HTML locais marcados como 'Lei'.
    Usa a lógica do LawScraper para garantir chunks semânticos.
    """
    
    def __init__(self):
        self.scraper = LawScraper()
        
    async def process_file(self, file_path: str, original_filename: str) -> Dict[str, Any]:
        """
        Lê um arquivo HTML local e extrai texto estruturado.
        """
        logger.info(f"⚖️ Processando Lei em HTML: {original_filename}")
        
        try:
            path = Path(file_path)
            # Try UTF-8, fallback to CP1252 (Windows) then Latin-1 for Brazilian laws
            raw_bytes = path.read_bytes()
            try:
                content = raw_bytes.decode("utf-8")
            except UnicodeDecodeError:
                try:
                    logger.info(f"⚠️ Falha em UTF-8. Tentando CP1252 para {original_filename}")
                    content = raw_bytes.decode("cp1252")
                except UnicodeDecodeError:
                    logger.info(f"⚠️ Falha em CP1252. Tentando Latin-1 para {original_filename}")
                    content = raw_bytes.decode("latin-1")
            
            # Use scraper logic
            clean_text, chunks = self.scraper.parse_html_content(content, original_filename)
            
            return {
                "full_text": clean_text,
                "chunks": chunks,
                "status": "success",
                "total_articles": len(chunks)
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar HTML Law: {e}")
            return {
                "full_text": "",
                "chunks": [],
                "status": "error",
                "error": str(e)
            }

html_law_ingestor = HtmlLawIngestor()
