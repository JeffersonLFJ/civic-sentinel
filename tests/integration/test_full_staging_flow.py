import pytest
import httpx
from src.interfaces.api.main import app
import os
from src.core.database import db_manager

@pytest.mark.asyncio
async def test_api_quarantine_to_chat_flow(monkeypatch, tmp_path):
    """
    Testa o fluxo: POST Upload -> GET Staging -> POST Approve -> GET Chat.
    """
    # Override DB to avoid touching production
    db_path = tmp_path / "integration_test.db"
    chroma_path = tmp_path / "integration_chroma"
    chroma_path.mkdir()
    
    from src.config import settings
    monkeypatch.setattr(settings, "SQLITE_DB_PATH", db_path)
    monkeypatch.setattr(settings, "CHROMADB_DIR", chroma_path)
    
    # Manually ensure DB is initialized
    await db_manager.get_sqlite()
    
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        
        # 1. UPLOAD (Deve ir para quarentena)
        # Vamos criar um arquivo fake
        file_content = b"Conteudo de uma lei municipal importante para teste de integracao."
        files = {'file': ('lei_municipal.txt', file_content, 'text/plain')}
        data = {'source': 'integration_test', 'doc_type': 'lei_ordinaria', 'sphere': 'municipal'}
    
        response = await client.post("/api/upload/", data=data, files=files)
        assert response.status_code == 200
        res_data = response.json()
        doc_id = res_data["doc_id"]
        
        # 2. VERIFICAR QUARENTENA
        staging_res = await client.get("/api/admin/staging")
        assert staging_res.status_code == 200
        staging_docs = staging_res.json()["documents"]
        
        assert any(d["id"] == doc_id for d in staging_docs)
        
        # 3. VERIFICAR CHAT (NÃO deve achar ainda)
        # Mock LLM calls if needed, but here we check citations
        # 3. Chat RAG (Agora com ID aprovado)
        chat_res = await client.post("/api/chat/", json={
            "message": "Quais são os documentos sobre vacinação?",
            "user_id": "test_user",
            "stream": False # Disable streaming for reliable JSON parsing in test
        })
        # Não podemos garantir 100% que o LLM não alucine, mas podemos checar os logs de auditoria ou metadados de fontes
        # O sistema retorna metadados de citações.
        assert doc_id not in [s.get("doc_id") for s in chat_res.json()["metadata"].get("citations", [])]
        
        # 4. APROVAR NA QUARENTENA
        approve_data = {
            "doc_type": "lei_ordinaria",
            "sphere": "municipal",
            "publication_date": "2023-12-29"
        }
        approve_res = await client.post(f"/api/admin/staging/{doc_id}/approve", json=approve_data)
        assert approve_res.status_code == 200
        
        # 5. VERIFICAR CHAT (AGORA deve achar)
        # Como o chat usa LLM, vamos testar apenas a recuperação documental se possível, 
        # ou confiar que o chat_endpoint chama a busca que agora inclui o doc.
        chat_res_post = await client.post("/api/chat/", json={
            "message": "lei municipal importante", 
            "user_id": "tester",
            "stream": False
        })
        citations = chat_res_post.json()["metadata"].get("citations", [])
        assert any(c["filename"] == "lei_municipal.txt" for c in citations)
