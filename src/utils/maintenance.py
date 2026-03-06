import os
import time
import logging
import asyncio
from pathlib import Path
from src.config import settings

logger = logging.getLogger(__name__)

async def cleanup_stale_uploads(max_age_seconds: int = 86400):
    """
    Remove arquivos da pasta temporária de uploads que sejam mais antigos que max_age_seconds (padrão 24h).
    """
    upload_dir = Path("data/uploads_temp")
    if not upload_dir.exists():
        return

    logger.info("🧹 Iniciando limpeza automática de uploads temporários...")
    count = 0
    now = time.time()

    for item in upload_dir.iterdir():
        if item.is_file():
            try:
                stat = item.stat()
                age = now - stat.st_mtime
                if age > max_age_seconds:
                    item.unlink()
                    count += 1
                    logger.debug(f"Arquivo removido (expirado): {item.name}")
            except Exception as e:
                logger.warning(f"Erro ao limpar arquivo {item.name}: {e}")

    if count > 0:
        logger.info(f"✅ Limpeza concluída: {count} arquivos expirados removidos.")
    else:
        logger.info("✅ Limpeza concluída: Nenhum arquivo expirado encontrado.")

async def cleanup_stale_uploads_periodically(interval_seconds: int = 3600, max_age_seconds: int = 86400):
    """
    Periodically cleans stale uploads to avoid storage bloat.
    """
    while True:
        try:
            await cleanup_stale_uploads(max_age_seconds=max_age_seconds)
        except Exception as e:
            logger.warning(f"Erro na limpeza periódica de uploads: {e}")
        await asyncio.sleep(interval_seconds)
