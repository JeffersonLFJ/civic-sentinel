from typing import Dict, Literal, Optional, Any
from pathlib import Path
import asyncio
from datetime import datetime
import logging
from src.config import settings

# Processors
# Tesseract Removed as per user request (Docling is primary, Vision is fallback)
from src.core.llm_client import llm_client

logger = logging.getLogger(__name__)

OCRMethod = Literal["docling", "gemma_vision", "direct_read"] # Simplified
DocumentType = Literal["diario_oficial", "orcamento", "foto_denuncia", "text_file", "auto"]

class OCREngine:
    """
    Simplified Engine: Primary role is now handling Vision Fallback.
    """
    
    def __init__(self):
        # Tesseract removed.
        pass
        
    @property
    def validation_threshold(self) -> float:
        from src.core.settings_manager import settings_manager
        return settings_manager.ocr_validation_threshold

    async def process_document(
        self, 
        file_path: str,
        doc_type: DocumentType = "auto",
        enable_validation: bool = True
    ) -> Dict[str, Any]:
        """
        Executes Vision Logic for images/fallbacks.
        """
        start_time = datetime.now()
        
        # 1. Detect Type (if auto)
        if doc_type == "auto":
            doc_type = self._detect_document_type(file_path)
            
        ocr_result = {"text": "", "method": "none", "confidence": 0.0}
        
        # 2. Logic: Only support Vision (foto_denuncia) or Direct Read here.
        # Regular docs should go through Router -> Docling.
        
        if doc_type == "foto_denuncia":
             # Non-document image (scene, artistic, pollution, etc) -> Direct to Vision
             logger.info(f"Detected {doc_type}. Using Gemma Vision directly.")
             try:
                 vision_response = await llm_client.generate(
                    prompt="Descreva esta imagem com detalhes e transcreva qualquer texto visível.",
                    images=[file_path]
                 )
                 ocr_result = {
                     "text": vision_response["content"],
                     "method": f"gemma_vision_direct_{vision_response['model']}",
                     "confidence": 0.85
                 }
             except Exception as e:
                 logger.error(f"Gemma Vision direct failed: {e}")
                 ocr_result = {"text": "", "method": "failed", "confidence": 0.0}
        
        elif doc_type == "text_file":
            # Direct Read Fallback
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                     ocr_result = {"text": f.read(), "method": "direct_read", "confidence": 1.0}
            except:
                pass

        # If we are here with "document" type in OCREngine, it implies Router sent us here as fallback?
        # Or legacy code. We assume fallback context if called purely for OCR.
        # But if it's a PDF/Image that Docling failed, we want Vision.
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return {
            "extracted_text": ocr_result["text"],
            "ocr_method": ocr_result["method"],
            "confidence": ocr_result["confidence"],
            "document_type": doc_type,
            "processing_time_ms": processing_time,
            "timestamp": datetime.utcnow().isoformat()
        }

    def _detect_document_type(self, file_path: str) -> DocumentType:
        if file_path.lower().endswith((".txt", ".html", ".htm")):
            return "text_file"
        # Everything else is potentially a photo/image for Vision if we are calling this Engine
        return "foto_denuncia"

ocr_engine = OCREngine() 

