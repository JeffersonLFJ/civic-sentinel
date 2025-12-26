from fastapi import APIRouter
from src.core.database import db_manager
from src.core.llm_client import llm_client
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/")
async def health_check():
    """
    Checks system status and dependencies.
    """
    status = {
        "status": "online",
        "database": "unknown",
        "llm": "unknown"
    }

    # Check Database
    try:
        await db_manager.get_sqlite()
        # Trigger Chroma client loading
        _ = db_manager.chroma_client 
        status["database"] = "connected"
    except Exception as e:
        status["database"] = f"error: {str(e)}"
        logger.error(f"Health check DB error: {e}")

    # Check LLM via simple ping/version or just assumption it's running
    # We won't block health on LLM availability to allow startup even if Ollama is down/loading
    status["llm"] = "configured" 

    return status
