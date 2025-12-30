import pytest
import datetime
from unittest.mock import AsyncMock, patch, MagicMock
from src.ingestors.diario_oficial import QueridoDiarioIngestor

@pytest.mark.asyncio
async def test_ingestor_dedup_and_store():
    """
    Test deduplication logic and storage of fetched gazettes.
    """
    ingestor = QueridoDiarioIngestor()
    
    # Mock date
    today = datetime.date.today().isoformat()
    
    # 1. Prepare Mock Data (2 entries for same day, later one prevails?)
    # The logic in process_and_store maps by date. Last one overwrites.
    gazettes_data = [
        {
            "date": today,
            "territory_id": "3303500",
            "territory_name": "Nova Iguacu",
            "url": "http://pdf.com/1",
            "txt_url": "http://txt.com/1",
            "scraped_at": "2023-01-01T10:00:00",
            "file_checksum": "hash1"
        },
        {
            "date": today, # Same date
            "territory_id": "3303500",
            "territory_name": "Nova Iguacu",
            "url": "http://pdf.com/2", # Unique URL (maybe updated version)
            "txt_url": "http://txt.com/2",
            "scraped_at": "2023-01-01T12:00:00", # Later scrape
            "file_checksum": "hash2"
        }
    ]
    
    # 2. Mock Dependencies
    mock_response = AsyncMock()
    mock_response.text = "Conteúdo do Diário Oficial Mockado"
    mock_response.raise_for_status = MagicMock()
    ingestor.client.get = AsyncMock(return_value=mock_response)
    
    # Patch db_manager (imported inside the method)
    # We patch where it is IMPORTED -> src.ingestors.diario_oficial.db_manager?
    # No, the code does: `from src.core.database import db_manager`.
    # So we patch `src.core.database.db_manager` (if it's a global instance).
    # OR we patch `src.ingestors.diario_oficial.db_manager` IF it was imported at top level.
    # It is NOT imported at top level. It's imported inside.
    # So we patch `src.core.database.db_manager`.
    
    with patch("src.core.database.db_manager") as mock_db:
        mock_db.save_document_record = AsyncMock(return_value="doc_123")
        mock_db.index_document_text = AsyncMock()
        
        # 3. Execution
        await ingestor.process_and_store(gazettes_data, keywords=[])
        
        # 4. Assertions
        
        # Deduplication Check:
        # process_and_store iterates unique_gazettes.
        # Since logic is "Last one wins" in the loop for `dedup_map`.
        # Should call save ONLY ONCE for this date (hash2).
        
        assert mock_db.save_document_record.call_count == 1
        # index_document_text is bypassed for staging area
        # assert mock_db.index_document_text.call_count == 1
        
        # Verify content download
        ingestor.client.get.assert_called() 
        args, _ = mock_db.save_document_record.call_args
        saved_doc = args[0]
        
        assert saved_doc["text_content"] == "Conteúdo do Diário Oficial Mockado"
        assert saved_doc["url"] == "http://pdf.com/2" # confirming it kept the second one
        assert saved_doc["source"] == "official_gazette"
