import pytest
from unittest.mock import AsyncMock, MagicMock
import sys
from pathlib import Path

# Fix path to allow importing src
sys.path.append(str(Path(__file__).parent.parent))

from src.core.database import DatabaseManager
from src.core.ocr_engine import OCREngine

@pytest.fixture
def mock_llm_client():
    mock = AsyncMock()
    # Default behavior for generate
    mock.generate.return_value = {
        "content": "Mocked LLM Response",
        "model": "gemma3:mock",
        "timestamp": "2023-01-01"
    }
    return mock

@pytest.fixture
def mock_tesseract():
    mock = AsyncMock()
    mock.extract.return_value = {
        "text": "Tesseract Text",
        "confidence": 95.0,
        "method": "tesseract"
    }
    return mock

@pytest.fixture
def mock_db_manager():
    mock = AsyncMock(spec=DatabaseManager)
    mock.save_document_record.return_value = "mock_doc_id"
    return mock
