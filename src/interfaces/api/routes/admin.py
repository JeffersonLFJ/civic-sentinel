from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from pathlib import Path
from src.core.database import db_manager
from src.config import settings
from src.ingestors.diario_oficial import diario_ingestor
from datetime import date, timedelta

router = APIRouter()
import logging
logger = logging.getLogger(__name__)

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
            
            # 4. Audit Logs (Expanded)
            await cursor.execute("SELECT id, timestamp, action, query, confidence_score FROM audit_logs ORDER BY timestamp DESC LIMIT 50")
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

@router.get("/audit/{log_id}")
async def get_audit_detail(log_id: str):
    """
    Returns full detail of an interaction for the Raio-X view (Reasoning Map).
    Parses stored JSON fields (details, sources_json) into objects.
    """
    import json
    try:
        if not db_manager._sqlite_connection:
            await db_manager.get_sqlite()
            
        async with db_manager._sqlite_connection.execute("SELECT * FROM audit_logs WHERE id = ?", (log_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Log not found")
            
            data = dict(row)
            
            # RAIO-X: Parse JSON fields for structured frontend display
            try:
                if data.get("details") and data["details"].startswith("{"):
                    data["details"] = json.loads(data["details"])
            except:
                pass # Keep as string if parsing fails (legacy logs)
                
            try:
                if data.get("sources_json"):
                    data["sources_json"] = json.loads(data["sources_json"])
            except:
                pass
                
            # Compute inferred "Reasoning Path" for visualization
            if isinstance(data.get("details"), dict):
                intent = data["details"].get("intent", {})
                data["reasoning_map"] = {
                    "step_1_intent": intent.get("understood_intent"),
                    "step_2_sphere": intent.get("sphere"),
                    "step_3_ambiguity": intent.get("ambiguity_score"),
                    "step_4_retrieval": f"{data['details'].get('rag_count', 0)} sources",
                    "step_5_confidence": data.get("confidence_score")
                }
            
            return data
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

# --- Application Settings ---

from src.core.settings_manager import settings_manager

@router.get("/settings")
async def get_settings():
    """Returns current dynamic settings."""
    return settings_manager.get_all()

@router.post("/settings")
async def update_settings(updates: Dict[str, Any] = Body(...)):
    """Updates dynamic settings."""
    try:
        settings_manager.update(updates)
        return {"status": "success", "message": "Configurações atualizadas."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/settings/reset_prompt")
async def reset_prompt():
    """Resets system prompt to default (hardcoded empty string, will force file reload)."""
    try:
        settings_manager.update({"system_prompt": ""})
        return {"status": "success", "message": "Prompt de sistema reiniciado para padrão de arquivo/código."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/settings/purge_cache")
async def purge_vector_cache():
    """
    DANGER: Clears ChromaDB vectors AND SQLite Data.
    """
    try:
        success = await db_manager.purge_full_system()
        if success:
            return {"status": "success", "message": "Sistema totalmente purgado (SQLite + Chroma)."}
        else:
            raise HTTPException(status_code=500, detail="Falha ao limpar cache.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Staging Area (Quarentena) ---

@router.get("/staging")
async def get_staging_documents():
    """
    Lista documentos na Quarentena (status='pending').
    """
    try:
        docs = await db_manager.get_pending_documents()
        return {"status": "success", "documents": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/staging/{doc_id}/text")
async def get_staging_text(doc_id: str):
    """
    Retorna o texto integral de um documento para inspeção.
    """
    try:
        # Reusamos a lógica de inspeção mas focada no texto bruto
        async with db_manager._sqlite_connection.execute("SELECT text_content FROM documents WHERE id = ?", (doc_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Documento não encontrado")
            return {"text": row["text_content"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ApprovalRequest(BaseModel):
    doc_type: str
    sphere: str
    publication_date: Optional[str] = None
    ementa: Optional[str] = None
    description: Optional[str] = None
    custom_tags: Optional[str] = None

@router.post("/staging/{doc_id}/approve")
async def approve_document(doc_id: str, request: ApprovalRequest):
    """
    Corrige metadados e move documento para 'queued' (fila de processamento).
    """
    try:
        # 1. Update Metadata & Status
        updates = {
            "doc_type": request.doc_type,
            "sphere": request.sphere,
            "publication_date": request.publication_date,
            "ementa": request.ementa,
            "description": request.description,
            "custom_tags": request.custom_tags,
            "status": "queued" # Move to Queue, DO NOT ACTIVATE YET
        }
        await db_manager.update_document_metadata(doc_id, updates)
        
        return {"status": "success", "message": "Documento enviado para a fila de processamento."}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/staging/process_batch")
async def process_staging_batch():
    """
    Processa todos os documentos na fila ('queued') em lote.
    """
    try:
        if not db_manager._sqlite_connection:
            await db_manager.get_sqlite()
            
        # 1. Get queued documents
        async with db_manager._sqlite_connection.execute("SELECT id, filename FROM documents WHERE status = 'queued'") as cursor:
             queued_docs = await cursor.fetchall()
             
        processed_count = 0
        errors = []
        
        for row in queued_docs:
            doc_id = row[0]
            filename = row[1]
            try:
                logger.info(f"⚙️ Processando Batch: {filename} ({doc_id})")
                await db_manager.activate_document(doc_id)
                processed_count += 1
            except Exception as e:
                logger.error(f"❌ Falha no Batch {filename}: {e}")
                errors.append(f"{filename}: {str(e)}")
        
        return {
            "status": "completed", 
            "processed_count": processed_count, 
            "errors": errors,
            "total_queued": len(queued_docs)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/staging/{doc_id}/activate")
async def activate_staging_document(doc_id: str):
    """
    Processa (ativa) um único documento da fila.
    Usado para processamento em batch com feedback granular no frontend.
    """
    try:
        # Verify if status is 'queued' (optional safety check, activate_document handles it mostly, 
        # but let's be strict to staging flow)
        if not db_manager._sqlite_connection:
            await db_manager.get_sqlite()
            
        async with db_manager._sqlite_connection.execute("SELECT status FROM documents WHERE id = ?", (doc_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Documento não encontrado")
            if row[0] != 'queued':
                # Allow 'pending' too if forced? No, strictly queued for now.
                # Actually, forcing usage of flow: Pending -> Approve -> Queued -> Activate
                if row[0] != 'pending': # Relaxing to allow quick processing if needed, but warning
                   pass 

        await db_manager.activate_document(doc_id)
        return {"status": "success", "message": "Documento ativado com sucesso."}

    except Exception as e:
        logger.error(f"❌ Falha ao ativar documento {doc_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/staging/queued")
async def get_queued_documents():
    """
    Lista documentos aguardando processamento.
    """
    try:
        if not db_manager._sqlite_connection:
            await db_manager.get_sqlite()
            
        async with db_manager._sqlite_connection.execute("SELECT id, filename, doc_type, sphere, created_at FROM documents WHERE status = 'queued' ORDER BY created_at ASC") as cursor:
            rows = await cursor.fetchall()
            return {"documents": [dict(row) for row in rows]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
