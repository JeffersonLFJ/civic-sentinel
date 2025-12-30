import pytest
import os
import shutil
from pathlib import Path
from src.core.database import DatabaseManager
from src.config import settings

@pytest.fixture
async def temp_db_manager(tmp_path, monkeypatch):
    """
    Cria um DatabaseManager com caminhos temporários para teste.
    """
    db_path = tmp_path / "test_sentinela.db"
    chroma_path = tmp_path / "test_chroma"
    chroma_path.mkdir()
    
    # Monkeypatch settings
    monkeypatch.setattr(settings, "SQLITE_DB_PATH", db_path)
    monkeypatch.setattr(settings, "CHROMADB_DIR", chroma_path)
    
    db = DatabaseManager()
    yield db
    
    # Cleanup
    if db._sqlite_connection:
        await db._sqlite_connection.close()

@pytest.mark.asyncio
async def test_staging_quarantine_isolation(temp_db_manager):
    """
    Verifica se documentos 'pending' não são indexados e não aparecem na busca normal.
    """
    db = temp_db_manager
    doc_id = "test_quarantine_01"
    doc_data = {
        "id": doc_id,
        "filename": "lei_teste_quarentena.pdf",
        "source": "manual",
        "text_content": "Esta é uma lei de teste que deve ficar na quarentena.",
        "ocr_method": "test",
        "doc_type": "lei_ordinaria",
        "sphere": "municipal",
        "status": "pending"
    }
    
    # 1. Salva registro
    actual_id = await db.save_document_record(doc_data)
    
    # 2. Verifica se está no banco pendente
    pending = await db.get_pending_documents()
    assert any(d["id"] == actual_id for d in pending)
    
    # 3. Verifica se NÃO está no ChromaDB (Busca vetorial deve vir vazia)
    # search_documents usa status='active' por padrão na nossa lógica de busca (precisamos garantir isso)
    results = await db.search_documents("lei de teste", limit=5)
    # Se resultados vierem, não devem conter nosso doc pendente
    assert all(r["metadata"].get("original_doc_id") != doc_id for r in results)

@pytest.mark.asyncio
async def test_staging_activation_flow(temp_db_manager):
    """
    Verifica o fluxo completo de ativação (Pending -> Active + Indexação).
    """
    db = temp_db_manager
    doc_id = "test_activation_01"
    doc_data = {
        "id": doc_id,
        "filename": "doc_ativacao.txt",
        "source": "manual",
        "text_content": "Conteúdo secreto para ativação.",
        "ocr_method": "test",
        "doc_type": "decreto",
        "sphere": "estadual",
        "status": "pending"
    }
    
    actual_id = await db.save_document_record(doc_data)
    
    # 1. Ativa documento
    success = await db.activate_document(actual_id)
    assert success is True
    
    # 2. Verifica status no banco
    async with (await db.get_sqlite()).execute("SELECT status FROM documents WHERE id = ?", (doc_id,)) as cursor:
        row = await cursor.fetchone()
        assert row["status"] == "active"
    
    # 3. Verifica se agora aparece na busca vetorial
    # (Damos um pequeno tempo se necessário, mas Chroma local costuma ser imediato)
    results = await db.search_documents("Conteúdo secreto", limit=5)
    assert any("secret" in r["content"] for r in results) # Busca semântica básica
