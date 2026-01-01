import logging
from pathlib import Path
from typing import Dict, Any

# Conditional import to avoid crashing if installed in background
try:
    from docling.document_converter import DocumentConverter
except ImportError:
    DocumentConverter = None

logger = logging.getLogger(__name__)

class DoclingProcessor:
    """
    Processador de documentos usando Docling.
    Converte PDF/Imagens/Docx para Markdown estruturado, preservando tabelas e layout.
    """
    
    def __init__(self):
        if DocumentConverter:
            self.converter = DocumentConverter()
        else:
            self.converter = None
            logger.warning("Docling não está instalado ou falhou ao importar.")

    async def process(self, file_path: str) -> Dict[str, Any]:
        """
        Converte o arquivo para Markdown.
        """
        if not self.converter:
             return {"text": "", "status": "error", "error": "Docling dependency missing"}

        try:
            logger.info(f"🤖 Docling processando: {file_path}")
            
            # Docling works synchronously effectively, but let's run it.
            # In a real async app we might want to run this in a threadpool if it's heavy.
            # For now, simple call.
            result = self.converter.convert(file_path)
            
            # Export to Markdown
            markdown_text = result.document.export_to_markdown()
            
            return {
                "extracted_text": markdown_text,
                "ocr_method": "docling_markdown",
                "confidence": 100.0, # Docling doesn't give simple confidence, assume high
                "metadata": {
                    "conversion_method": "docling"
                }
            }
            
        except Exception as e:
            logger.error(f"Erro no Docling: {e}")
            return {
                "extracted_text": "",
                "status": "error",
                "error": str(e)
            }

docling_processor = DoclingProcessor()
