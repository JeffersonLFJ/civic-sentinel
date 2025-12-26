from typing import Dict, Literal, Optional, Any
from pathlib import Path
import asyncio
from datetime import datetime
import logging
from src.config import settings

# Processors
from src.ocr.tesseract_processor import TesseractOCR
# Placeholders for future implementations
# from src.ocr.paddle_processor import PaddleOCR 
# from src.ocr.doctr_processor import DocTROCR
from src.core.llm_client import llm_client

logger = logging.getLogger(__name__)

OCRMethod = Literal["tesseract", "paddle", "doctr", "gemma_vision", "auto", "hybrid", "pass_through"]
DocumentType = Literal["diario_oficial", "orcamento", "foto_denuncia", "text_file", "auto"]

class OCREngine:
    """
    Centralized OCR manager with adaptive fallback.
    """
    
    def __init__(self):
        self.tesseract = TesseractOCR(config=settings.model_dump())
        # self.paddle = ...
        # self.doctr = ...
        
        self.MIN_CONFIDENCE = settings.OCR_MIN_CONFIDENCE
        self.VALIDATION_THRESHOLD = settings.OCR_VALIDATION_THRESHOLD

    async def process_document(
        self, 
        file_path: str,
        doc_type: DocumentType = "auto",
        enable_validation: bool = True
    ) -> Dict[str, Any]:
        """
        Process document with intelligent cascade:
        1. Detect Type (if auto)
        2. If 'foto_denuncia' (scene/non-text): Skip OCR, use Gemma Vision.
        3. If 'document': Run Tesseract.
        4. If Tesseract low confidence: Trigger Gemma Vision fallback.
        """
        start_time = datetime.now()
        
        # 1. Detect Type
        if doc_type == "auto":
            doc_type = self._detect_document_type(file_path)
            
        ocr_result = {"text": "", "method": "none", "confidence": 0.0}
        validation_result = None

        # 2. Decision Logic
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
                     "confidence": 0.85 # Estimated high confidence for direct vision
                 }
             except Exception as e:
                 logger.error(f"Gemma Vision direct failed: {e}")
                 ocr_result = {"text": "", "method": "failed", "confidence": 0.0}

        elif doc_type == "text_file":
            # Text files -> Direct Read
            try:
                ocr_result = await self._execute_ocr(file_path, "pass_through")
            except Exception as e:
                logger.error(f"Text read failed: {e}")
                ocr_result = {"text": "", "method": "read_failed", "confidence": 0.0}

        elif doc_type == "pdf_text":
            # Native PDF -> Direct Extraction
            try:
                ocr_result = await self._execute_ocr(file_path, "pdf_direct")
            except Exception as e:
                logger.error(f"PDF direct read failed: {e}")
                ocr_result = {"text": "", "method": "pdf_read_failed", "confidence": 0.0}

        else:
            # Standard Document -> Try Tesseract first (Fast)
            try:
                ocr_result = await self._execute_ocr(file_path, "tesseract")
            except Exception as e:
                logger.error(f"Tesseract failed: {e}")
                ocr_result = {"text": "", "method": "tesseract_failed", "confidence": 0.0}

            # 3. Validation / Fallback logic for Documents
            # Only trigger fallback if confidence is low AND we haven't already used Vision
            if enable_validation and ocr_result["confidence"] < self.VALIDATION_THRESHOLD:
                logger.info(f"Low confidence ({ocr_result['confidence']}). Triggering Gemma Vision fallback.")
                try:
                    # Use LLM Vision to extract text
                    vision_response = await llm_client.generate(
                        prompt="Transcreva todo o texto visível nesta imagem. Retorne apenas o texto transcrito, sem comentários.",
                        images=[file_path]
                    )
                    
                    # We can merge or replace. For now, let's treat it as a refined result
                    ocr_result["text"] = vision_response["content"]
                    ocr_result["method"] = f"tesseract_fallback_{vision_response['model']}"
                    ocr_result["confidence"] = 0.90 # Artificial confidence for Manual/AI fix
                    validation_result = "fallback_triggered"
                    
                except Exception as e:
                    logger.error(f"Gemma Vision fallback failed: {e}")
                    validation_result = f"fallback_failed: {str(e)}"

        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return {
            "extracted_text": ocr_result["text"],
            "ocr_method": ocr_result["method"],
            "confidence": ocr_result["confidence"],
            "document_type": doc_type,
            "validation": validation_result,
            "processing_time_ms": processing_time,
            "timestamp": datetime.utcnow().isoformat()
        }

    def _detect_document_type(self, file_path: str) -> DocumentType:
        """
        Simple heuristic detection.
        """
        # TODO: Implement more robust detection (e.g. using a small classifier model)
        # For now, we assume PDF -> document, Image -> Check extension/content?
        # Actually, let's assume images are 'foto_denuncia' unless explicitly claimed otherwise
        # But users upload photos of documents.
        # Ideally we'd run a quick classifier. 
        # Heuristic: If we can assume most user uploads are documents, default to document.
        # But user specifically asked for "river pollution" etc.
        # Let's defaulting to 'document' for now, but allowing 'foto_denuncia' override if logic allows.
        # ACTUALLY, strict requirement: "Image with low quality -> Check logs".
        # Let's rely on Tesseract: if it finds no text (conf near 0), it's likely a non-doc image -> Vision.
        # Refined Logic above handles low conv -> Vision.
        # This covers the "non-document" case effectively via fallback!
        # However, to be "Efficient" and skip Tesseract for "Artistic", we need pre-detection.
        # Without a pre-trained model, accurate pre-detection is hard.
        # COMPROMISE: Default to 'document'. If it's a scene, Tesseract will produce garbage/low conf -> Fallback triggers Vision.
        # This satisfies the requirement safely.
        
        if file_path.lower().endswith(".pdf"):
            try:
                import PyPDF2
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    if len(reader.pages) > 0:
                        text = reader.pages[0].extract_text()
                        if text and len(text.strip()) > 100:
                            return "pdf_text"
            except Exception as e:
                logger.warning(f"PDF text check failed: {e}")
            
            return "diario_oficial"
        if file_path.lower().endswith((".txt", ".html", ".htm")):
            return "text_file"
        return "document" # Default to document, let fallback handle scenes as 'low text confidence'

    async def _execute_ocr(
        self, 
        file_path: str, 
        method: OCRMethod
    ) -> Dict:
        if method == "pass_through":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return {
                    "text": f.read(),
                    "confidence": 100.0,
                    "method": "direct_read"
                }
        elif method == "pdf_direct":
            try:
                import PyPDF2
                text = ""
                with open(file_path, 'rb') as f:
                    pdf = PyPDF2.PdfReader(f)
                    for page in pdf.pages:
                        text += page.extract_text() + "\n"
                return {
                    "text": text,
                    "confidence": 100.0,
                    "method": "pdf_direct_extract"
                }
            except Exception as e:
                 logger.error(f"PDF direct extraction failed: {e}")
                 # Fallback to Tesseract?
                 return {"text": "", "confidence": 0.0, "method": "failed"}

        elif method == "tesseract":
            return await self.tesseract.extract(file_path)
        elif method == "gemma_vision":
             # Placeholder for LLM vision extraction
             return {"text": "", "confidence": 0, "method": "gemma_vision"}
        
        return {"text": "", "confidence": 0, "error": "Unknown method"}

ocr_engine = OCREngine()
