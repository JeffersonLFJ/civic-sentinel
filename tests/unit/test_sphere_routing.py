import pytest
from src.core.database import DatabaseManager
from src.config import settings

@pytest.fixture
async def temp_db_manager(tmp_path, monkeypatch):
    db_path = tmp_path / "test_sphere.db"
    chroma_path = tmp_path / "test_chroma_sphere"
    chroma_path.mkdir()
    
    monkeypatch.setattr(settings, "SQLITE_DB_PATH", db_path)
    monkeypatch.setattr(settings, "CHROMADB_DIR", chroma_path)
    
    db = DatabaseManager()
    yield db
    if db._sqlite_connection:
        await db._sqlite_connection.close()

@pytest.mark.asyncio
async def test_sphere_filtering_sqlite(temp_db_manager):
    """
    Testa se o filtro de esfera funciona na busca lexical (FTS5).
    """
    db = temp_db_manager
    
    # 1. Ingerir dois docs de esferas diferentes
    total_docs = [
        {"id": "doc_fed", "filename": "uniao.txt", "source": "test", "text_content": "Diretrizes Federais de Saúde", "sphere": "federal", "status": "active", "ocr_method": "manual"},
        {"id": "doc_mun", "filename": "cidade.txt", "source": "test", "text_content": "Diretrizes Municipais de Saúde", "sphere": "municipal", "status": "active", "ocr_method": "manual"}
    ]
    
    for d in total_docs:
        await db.save_document_record(d)
        
    # 2. Busca com filtro 'federal'
    results_fed = await db.search_documents_keyword("Diretrizes", sphere="federal")
    assert len(results_fed) == 1
    assert results_fed[0]["metadata"]["filename"] == "uniao.txt"
    
    # 3. Busca com filtro 'municipal'
    results_mun = await db.search_documents_keyword("Diretrizes", sphere="municipal")
    assert len(results_mun) == 1
    assert results_mun[0]["metadata"]["filename"] == "cidade.txt"

@pytest.mark.asyncio
async def test_sphere_filtering_chroma(temp_db_manager):
    """
    Testa se o filtro de esfera funciona na busca semântica (ChromaDB).
    """
    db = temp_db_manager
    
    # Ingerir e indexar (usando activate_document para garantir o fluxo real)
    docs = [
        {"id": "s1", "filename": "federal.txt", "text_content": "Vacinação Nacional", "sphere": "federal", "status": "pending", "source": "test"},
        {"id": "s2", "filename": "local.txt", "text_content": "Vacinação de Bairro", "sphere": "municipal", "status": "pending", "source": "test"}
    ]
    
    for d in docs:
        actual_id = await db.save_document_record(d)
        await db.activate_document(actual_id)
        
    # Busca 'Vacinação' filtrada por 'municipal'
    results = await db.search_documents("Vacinação", sphere="municipal", limit=1)
    assert len(results) > 0
    assert results[0]["metadata"]["sphere"] == "municipal"
    assert "Bairro" in results[0]["content"]
