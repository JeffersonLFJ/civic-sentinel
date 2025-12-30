import pytest
from unittest.mock import AsyncMock, patch
from src.interfaces.api.routes.chat import chat_endpoint, ChatRequest
from src.core.reranker import reranker

@pytest.mark.asyncio
async def test_hybrid_flow_logic():
    """
    Testa se o fluxo Híbrido (Vector + Keyword) -> Rerank é acionado corretamente.
    NÃO testa o modelo real (pesado), apenas a lógica de orquestração.
    """
    
    # 1. Mock DB Manager to return dummy results for both Vector and Keyword
    with patch("src.core.database.db_manager") as mock_db:
        mock_db.search_documents = AsyncMock(return_value=[
            {"content": "Texto Vetorial 1", "metadata": {"filename": "doc_vec.txt", "doc_id": "1", "source": "test"}, "score": 0.8}
        ])
        
        # Keyword search returns full doc content, which logic splits
        mock_db.search_documents_keyword = AsyncMock(return_value=[
            {"content": "Texto Palavra-Chave Importante", "metadata": {"filename": "doc_key.txt", "doc_id": "2", "source": "test"}, "score": 0.5}
        ])
        
        # Log Audit must be async too
        mock_db.log_audit = AsyncMock(return_value="log_id_123")
        
        # 2. Mock Reranker to avoid loading PyTorch model
        with patch.object(reranker, "rerank", return_value=[
            {"index": 1, "score": 0.99, "content": "Texto Palavra-Chave Importante"}, # Keyword wins
            {"index": 0, "score": 0.10, "content": "Texto Vetorial 1"}
        ]) as mock_rerank:
            
            # 3. Mock LLM - now called TWICE (1. Intent, 2. Final Response) - HyDE is DISABLED
            with patch("src.core.llm_client.llm_client.generate", new_callable=AsyncMock) as mock_generate:
                # Side effect guarantees distinct returns for sequential calls
                mock_generate.side_effect = [
                    # Call 1: Intent Interpretation
                    {
                        "content": '{"ambiguity_score": 0.1, "formal_query": "Localizacao UBS", "keywords": ["posto", "saude", "localizacao"], "user_friendly_explanation": "onde fica o posto", "interjection": "Certo"}',
                        "model": "mock", "timestamp": "now"
                    },
                    # Call 2: Final Response
                    {"content": "Resposta Final", "model": "mock", "timestamp": "now"} 
                ]
                
                # Request
                req = ChatRequest(message="Onde fica o posto de saude?", user_id="user123", stream=False)
                response = await chat_endpoint(req)
                
                # Assertions
                
                # Verify Intent -> Response (HyDE skipped)
                assert mock_generate.call_count == 2
                
                # DB called?
                mock_db.search_documents.assert_called_once()
                args_vec, _ = mock_db.search_documents.call_args
                # Vector search should use ORIGINAL QUERY (since HyDE is disabled)
                assert args_vec[0] == "Onde fica o posto de saude?"
                
                mock_db.search_documents_keyword.assert_called_once()
                args_key, _ = mock_db.search_documents_keyword.call_args
                # Keyword search should use EXTRACTED KEYWORDS
                # We interpret the list equality slightly loosely or check if it matches what we mocked in Intent
                assert args_key[0] == ["posto", "saude", "localizacao"]
                
                # Rerank called with merged candidates?
                # We expect 2 candidates (1 vector + 1 chunk from keyword doc)
                args, _ = mock_rerank.call_args
                query, candidates = args[0], args[1]
                assert len(candidates) >= 2 
                assert "Texto Vetorial 1" in candidates
                # Note: Keyword text might have prefix added by splitter logic: "[doc_key.txt] Texto..."
                assert any("Texto Palavra-Chave" in c for c in candidates)
                
                # Check Verification: The response metadata citations should follow rerank order
                citations = response["metadata"]["citations"]
                # First citation should be the one with score 0.99 (The keyword one)
                assert citations[0]["relevance_score"] == 0.99
                assert "doc_key.txt" in citations[0]["filename"]
