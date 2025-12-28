from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict
from pydantic import BaseModel
from pathlib import Path
from src.core.database import db_manager
from src.config import settings
from src.ingestors.diario_oficial import diario_ingestor
from datetime import date, timedelta

router = APIRouter()

# --- Stats ---
@router.get("/stats")
async def get_system_stats():
    """
    Returns dashboard statistics.
    """
    try:
        if not db_manager._sqlite_connection:
            await db_manager.get_sqlite()
            
        async with db_manager._sqlite_connection.cursor() as cursor:
            # 1. Total Documents
            await cursor.execute("SELECT COUNT(*) FROM documents")
            total_docs = (await cursor.fetchone())[0]
            
            # 2. Docs by Source
            await cursor.execute("SELECT source, COUNT(*) FROM documents GROUP BY source")
            sources = {row[0]: row[1] for row in await cursor.fetchall()}
            
            # 3. Last Ingestion
            await cursor.execute("SELECT created_at FROM documents ORDER BY created_at DESC LIMIT 1")
            last_entry = await cursor.fetchone()
            last_ingestion = last_entry[0] if last_entry else "N/A"
            
            # 4. Audit Logs (New)
            await cursor.execute("SELECT timestamp, action, details, confidence_score FROM audit_logs ORDER BY timestamp DESC LIMIT 10")
            audit_logs = [dict(row) for row in await cursor.fetchall()]

        return {
            "total_documents": total_docs,
            "sources": sources,
            "last_ingestion": last_ingestion,
            "audit_logs": audit_logs,
            "system_health": "Healthy"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/audit")
async def clear_audit_logs():
    """
    Clears all audit logs.
    """
    try:
        count = await db_manager.clear_audit_logs()
        return {"status": "success", "message": f"Removidos {count} logs de auditoria."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Prompt Editor ---
PROMPT_FILE = settings.BASE_DIR / "sentinela_prompt_v2.md"

class PromptUpdate(BaseModel):
    content: str

@router.get("/inspect/{doc_id}")
async def inspect_document(doc_id: str):
    """
    Debug: View extracted chunks for a document.
    """
    return await db_manager.inspect_document(doc_id)

@router.get("/prompt")
async def get_system_prompt():
    """
    Reads the active system prompt file.
    """
    try:
        if not PROMPT_FILE.exists():
            return {"content": "# Prompt file not found"}
        return {"content": PROMPT_FILE.read_text(encoding="utf-8")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/prompt")
async def update_system_prompt(update: PromptUpdate):
    """
    Updates the system prompt file.
    """
    try:
        PROMPT_FILE.write_text(update.content, encoding="utf-8")
        return {"status": "success", "message": "Prompt atualizado com sucesso."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs")
async def get_system_logs(lines: int = 100):
    """
    Retrieves the last N lines of the application log file.
    """
    log_file = Path("data/app.log")
    if not log_file.exists():
        return {"logs": ["Log file not found."]}
    
    try:
        # Read last lines efficiently-ish
        content = log_file.read_text(encoding="utf-8").splitlines()
        return {"logs": content[-lines:]}
    except Exception as e:
        return {"logs": [f"Error reading logs: {str(e)}"]}

# --- Ingestion Control ---

class IngestionRequest(BaseModel):
    days: int = 7
    keywords: list[str] = []

@router.post("/ingest/nova-iguacu")
async def trigger_nova_iguacu_ingestion(request: IngestionRequest = Body(...)):
    """
    Triggers the ingestion of Nova Iguaçu gazettes for the last N days.
    """
    try:
        since_date = date.today() - timedelta(days=request.days)
        
        # Trigger in background would be better for a real app, 
        # but here we'll await to give immediate feedback for the prototype.
        gazettes = await diario_ingestor.fetch_gazettes(
            since=since_date,
            keywords=request.keywords
        )
        
        if not gazettes:
            return {"status": "success", "message": "No new gazettes found."}
            
        await diario_ingestor.process_and_store(gazettes, keywords=request.keywords)
        
        return {
            "status": "success", 
            "message": f"Successfully ingested {len(gazettes)} gazettes from Nova Iguaçu.",
            "count": len(gazettes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ingest/list")
async def list_local_files():
    """
    Lista arquivos pendentes na pasta data/ingest.
    """
    from src.ingestors.local_folder import local_ingestor
    try:
        files = await local_ingestor.list_pending_files()
        return {"status": "success", "files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class LocalProcessRequest(BaseModel):
    items: List[Dict[str, str]] # [{"filename": "...", "doc_type": "..."}]

@router.post("/ingest/process")
async def process_local_files(request: LocalProcessRequest):
    """
    Processa arquivos selecionados com tipos específicos.
    """
    from src.ingestors.local_folder import local_ingestor
    try:
        results = await local_ingestor.process_selected_files(request.items)
        return {
            "status": "success",
            "message": f"Processamento concluído: {results['processed']} arquivos ingeridos.",
            "details": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
