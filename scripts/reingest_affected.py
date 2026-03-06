"""
Re-ingestion script for affected documents.
Deletes existing ChromaDB chunks and re-indexes with the fixed pipeline.

Usage: python -m scripts.reingest_affected
"""
import asyncio
import logging
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def reingest_all():
    from src.core.database import db_manager
    
    # Initialize connections
    await db_manager.get_sqlite()
    
    # 1. Get all active documents
    query = "SELECT id, filename, doc_type FROM documents WHERE status = 'active'"
    async with db_manager._sqlite_connection.execute(query) as cursor:
        docs = await cursor.fetchall()
    
    if not docs:
        logger.info("No active documents found.")
        return
    
    logger.info(f"Found {len(docs)} active documents to re-ingest.")
    
    # 2. Clear ALL ChromaDB chunks
    try:
        db_manager.chroma_client.delete_collection("sentinela_documents")
        logger.info("🗑️ ChromaDB collection deleted.")
    except Exception as e:
        logger.warning(f"Could not delete collection (may not exist): {e}")
    
    # Recreate empty collection
    db_manager.chroma_client.get_or_create_collection("sentinela_documents")
    logger.info("✅ Fresh ChromaDB collection created.")
    
    # 3. Clear parent chunks from SQLite
    try:
        await db_manager._sqlite_connection.execute("DELETE FROM doc_parents")
        await db_manager._sqlite_connection.commit()
        logger.info("🗑️ Parent chunks cleared from SQLite.")
    except Exception as e:
        logger.warning(f"Could not clear parents: {e}")
    
    # 4. Re-index each document
    success = 0
    failed = 0
    
    for row in docs:
        doc_id = row[0]
        filename = row[1]
        doc_type = row[2]
        
        logger.info(f"\n{'='*60}")
        logger.info(f"📄 Re-ingesting: {filename} (type: {doc_type})")
        
        try:
            # Reset status to queued, then activate (which triggers indexing)
            await db_manager._sqlite_connection.execute(
                "UPDATE documents SET status = 'queued' WHERE id = ?", (doc_id,)
            )
            await db_manager._sqlite_connection.commit()
            
            result = await db_manager.activate_document(doc_id)
            if result:
                success += 1
                logger.info(f"✅ {filename} re-indexed successfully.")
            else:
                failed += 1
                logger.error(f"❌ {filename} failed to re-index.")
        except Exception as e:
            failed += 1
            logger.error(f"❌ {filename} error: {e}")
    
    # 5. Final report
    col = db_manager.chroma_client.get_or_create_collection("sentinela_documents")
    
    logger.info(f"\n{'='*60}")
    logger.info(f"🏁 RE-INGESTION COMPLETE")
    logger.info(f"   Success: {success}")
    logger.info(f"   Failed:  {failed}")
    logger.info(f"   Total ChromaDB chunks: {col.count()}")

if __name__ == "__main__":
    asyncio.run(reingest_all())
