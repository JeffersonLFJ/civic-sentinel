import pytest
from unittest.mock import AsyncMock, patch
from src.core.ocr_engine import OCREngine

@pytest.mark.asyncio
async def test_ocr_cascade_happy_path(mock_tesseract):
    """
    Test standard document flow: Tesseract succeeds with high confidence.
    """
    with patch("src.core.ocr_engine.TesseractOCR") as MockTess:
        # Arrange
        engine = OCREngine()
        # Replace the instance created in __init__ with our mock
        engine.tesseract = mock_tesseract
        
        # Act
        result = await engine.process_document("doc.pdf", doc_type="document")
        
        # Assert
        # Should use Tesseract
        mock_tesseract.extract.assert_called_once()
        assert result["extracted_text"] == "Tesseract Text"
        assert result["ocr_method"] == "tesseract"
        assert result["validation"] is None # No fallback needed

@pytest.mark.asyncio
async def test_ocr_fallback_trigger(mock_tesseract, mock_llm_client):
    """
    Test fallback: Tesseract has low confidence -> Vision is triggered.
    """
    with patch("src.core.ocr_engine.llm_client", mock_llm_client):
        engine = OCREngine()
        
        # Arrange: Low confidence Tesseract
        mock_tesseract.extract.return_value = {
            "text": "Bad text",
            "confidence": 0.4, # Below 0.8 threshold
            "method": "tesseract"
        }
        engine.tesseract = mock_tesseract
        
        # Act
        result = await engine.process_document("doc.pdf", doc_type="document")
        
        # Assert
        # Tesseract called
        mock_tesseract.extract.assert_called_once()
        # Vision called (fallback)
        mock_llm_client.generate.assert_called_once()
        
        # Result should be from Vision
        assert result["extracted_text"] == "Mocked LLM Response"
        assert "tesseract_fallback" in result["ocr_method"]
        assert result["validation"] == "fallback_triggered"

@pytest.mark.asyncio
async def test_ocr_direct_vision_for_images(mock_llm_client):
    """
    Test direct routing for 'foto_denuncia'.
    """
    with patch("src.core.ocr_engine.llm_client", mock_llm_client):
        engine = OCREngine()
        # Mock tesseract to ensure it's NOT called
        engine.tesseract = AsyncMock() 
        
        # Act
        result = await engine.process_document("river.jpg", doc_type="foto_denuncia")
        
        # Assert
        engine.tesseract.extract.assert_not_called()
        mock_llm_client.generate.assert_called_once()
        assert "gemma_vision_direct" in result["ocr_method"]
