import pytesseract
from PIL import Image
import logging
from typing import Dict, Any
import os

logger = logging.getLogger(__name__)

class TesseractOCR:
    """
    Tesseract OCR implementation.
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        # Verify if tesseract is available
        try:
            pytesseract.get_tesseract_version()
            self.available = True
        except Exception:
            logger.warning("Tesseract not found. OCR capabilities will be limited.")
            self.available = False

    async def extract(self, file_path: str) -> Dict[str, Any]:
        """
        Extracts text from an image or PDF using Tesseract.
        """
        if not self.available:
            return {"text": "", "confidence": 0.0, "error": "Tesseract not installed"}

        try:
            # Check if file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            # Basic extraction
            text_parts = []
            confidences = []
            
            # Handle PDF vs Image
            if file_path.lower().endswith('.pdf'):
                try:
                    from pdf2image import convert_from_path, pdfinfo_from_path
                    
                    # Get info first (lightweight)
                    info = pdfinfo_from_path(file_path)
                    total_pages = int(info["Pages"])
                    logger.info(f"Start OCR for PDF: {total_pages} pages detected.")
                    
                    # Process page by page to save RAM and provide logs
                    for i in range(1, total_pages + 1):
                        logger.info(f"OCR em andamento: Processando página {i} de {total_pages}...")
                        
                        # Convert single page
                        pages = convert_from_path(file_path, first_page=i, last_page=i)
                        
                        for img in pages:
                            data = pytesseract.image_to_data(img, lang='por', output_type=pytesseract.Output.DICT)
                            
                            num_boxes = len(data['text'])
                            for j in range(num_boxes):
                                if int(data['conf'][j]) > -1:
                                    if data['text'][j].strip():
                                        text_parts.append(data['text'][j])
                                        confidences.append(int(data['conf'][j]))
                                        
                except ImportError:
                     return {"text": "", "confidence": 0.0, "error": "pdf2image/poppler not installed"}
                except Exception as e:
                     logger.error(f"OCR PDF loop failed at page {i if 'i' in locals() else '?'}: {e}")
                     # Return what we have so far? Or fail? Let's return partial text with error note.
                     return {
                         "text": " ".join(text_parts) + f"\n[ERRO PARCIAL: {str(e)}]", 
                         "confidence": 0.0, 
                         "error": str(e)
                     }
            else:
                # Assume Image
                images = [Image.open(file_path)]
                
                # Process each image (standard flow)
                for img in images:
                    data = pytesseract.image_to_data(img, lang='por', output_type=pytesseract.Output.DICT)
                    num_boxes = len(data['text'])
                    for j in range(num_boxes):
                         if int(data['conf'][j]) > -1:
                             if data['text'][j].strip():
                                 text_parts.append(data['text'][j])
                                 confidences.append(int(data['conf'][j]))
            
            full_text = " ".join(text_parts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            return {
                "text": full_text,
                "confidence": avg_confidence,
                "method": "tesseract"
            }
            
        except Exception as e:
            logger.error(f"Tesseract OCR failed: {str(e)}")
            return {"text": "", "confidence": 0.0, "error": str(e)}
