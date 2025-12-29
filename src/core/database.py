import chromadb
from chromadb.config import Settings as ChromaSettings
import aiosqlite
import logging
from typing import Dict, Any, List
from src.config import settings

# Logger setup
logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Centralized database manager for Vector (ChromaDB) and Relational (SQLite) data.
    """
    
    def __init__(self):
        self._chroma_client = None
        self._sqlite_connection = None

    @property
    def chroma_client(self):
        """
        Sync ChromaDB client (Chroma currently uses sync API for most ops, 
        or async via HTTP client but we are using persistent local).
        """
        if not self._chroma_client:
            logger.info(f"Connecting to ChromaDB at {settings.CHROMADB_DIR}")
            self._chroma_client = chromadb.PersistentClient(
                path=str(settings.CHROMADB_DIR),
                settings=ChromaSettings(anonymized_telemetry=False)
            )
        return self._chroma_client

    async def get_sqlite(self) -> aiosqlite.Connection:
        """
        Async SQLite connection factory.
        """
        if not self._sqlite_connection:
            logger.info(f"Connecting to SQLite at {settings.SQLITE_DB_PATH}")
            # Ensure directory exists
            settings.SQLITE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            
            self._sqlite_connection = await aiosqlite.connect(settings.SQLITE_DB_PATH)
            self._sqlite_connection.row_factory = aiosqlite.Row
            
            # Initialize schema if needed
            await self._init_sqlite_schema()
            
        return self._sqlite_connection

    async def _init_sqlite_schema(self):
        """
        Creates basic tables if they don't exist.
        """
        query_audit = """
        CREATE TABLE IF NOT EXISTS audit_logs (
            id TEXT PRIMARY KEY,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            action TEXT NOT NULL,
            details TEXT,
            user_hash TEXT NOT NULL,
            confidence_score REAL,
            query TEXT,
            response TEXT,
            sources_json TEXT
        );
        """
        
        query_users = """
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY, -- This is the anonymized hash
            risk_level TEXT DEFAULT 'low',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        query_docs = """
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            source TEXT NOT NULL, -- 'user' or 'admin' 
            storage_path TEXT, -- NULL if file was deleted (privacy)
            text_content TEXT,
            ocr_method TEXT,
            url TEXT, -- Source URL for citations (e.g. Querido Diário)
            publication_date DATE, -- Official publication date
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        async with self._sqlite_connection.cursor() as cursor:
            await cursor.execute(query_audit)
            await cursor.execute(query_users)
            await cursor.execute(query_docs)
            
            # FTS5 Virtual Table for Keyword Search
            query_fts = """
            CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                id UNINDEXED,
                text_content,
                filename,
                source,
                tokenize='porter'
            );
            """
            await cursor.execute(query_fts)
            
            # FTS Backfill Migration
            # Check if FTS is empty but documents has data
            try:
                await cursor.execute("SELECT COUNT(*) FROM documents_fts")
                count_fts = (await cursor.fetchone())[0]
                
                await cursor.execute("SELECT COUNT(*) FROM documents")
                count_docs = (await cursor.fetchone())[0]
                
                if count_docs > 0 and count_fts == 0:
                    logger.info("🔄 Migração FTS: Populando tabela virtual com documentos existentes...")
                    await cursor.execute("""
                        INSERT INTO documents_fts (id, text_content, filename, source)
                        SELECT id, text_content, filename, source FROM documents WHERE text_content IS NOT NULL
                    """)
                    logger.info("✅ Migração FTS concluída.")
            except Exception as e:
                logger.warning(f"⚠️ Falha na verificação/migração FTS: {e}")
            
            # Migration: Check if url column exists, if not add it (simple migration for dev)
            # ... (omitted standard migrations)
            # In a real app we would use alembic
            try:
                await cursor.execute("ALTER TABLE documents ADD COLUMN url TEXT")
            except Exception:
                pass # Column likely exists or table just created
                
            try:
                await cursor.execute("ALTER TABLE documents ADD COLUMN publication_date DATE")
            except Exception:
                pass

            try:
                await cursor.execute("ALTER TABLE audit_logs ADD COLUMN query TEXT")
            except Exception:
                pass

            try:
                await cursor.execute("ALTER TABLE audit_logs ADD COLUMN response TEXT")
            except Exception:
                pass

            try:
                await cursor.execute("ALTER TABLE audit_logs ADD COLUMN sources_json TEXT")
            except Exception:
                pass

            await self._sqlite_connection.commit()

    async def register_user_if_not_exists(self, user_hash: str):
        """
        Idempotent registration of anonymized user.
        """
        if not self._sqlite_connection:
            await self.get_sqlite()
            
        async with self._sqlite_connection.execute(
            "INSERT OR IGNORE INTO users (id) VALUES (?)", (user_hash,)
        ) as cursor:
            await self._sqlite_connection.commit()
    async def log_audit(self, action: str, user_hash: str, details: str = None, query_text: str = None, response_text: str = None, sources_json: str = None, confidence_score: float = None):
        """
        Logs an action to the audit trail with support for detailed RAG inspection.
        """
        if not self._sqlite_connection:
            await self.get_sqlite()
            
        import uuid
        log_id = str(uuid.uuid4())
        
        sql = """
        INSERT INTO audit_logs (id, action, details, user_hash, confidence_score, query, response, sources_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (log_id, action, details, user_hash, confidence_score, query_text, response_text, sources_json)
        
        async with self._sqlite_connection.execute(sql, params) as cursor:
            await self._sqlite_connection.commit()
            return log_id
            
    async def clear_audit_logs(self):
        """
        Clears all records from audit_logs table.
        """
        if not self._sqlite_connection:
            await self.get_sqlite()
            
        async with self._sqlite_connection.execute("DELETE FROM audit_logs") as cursor:
            await self._sqlite_connection.commit()
            return cursor.rowcount

    async def save_document_record(self, doc_data: Dict[str, Any]):
        """
        Saves document metadata and content.
        Also indexes into FTS.
        """
        if not self._sqlite_connection:
            await self.get_sqlite()
            
        import uuid
        doc_id = str(uuid.uuid4())
        
        query = """
        INSERT INTO documents (
            id, filename, source, storage_path, text_content, ocr_method, url, publication_date, doc_type
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            doc_id,
            doc_data["filename"],
            doc_data["source"],
            doc_data.get("storage_path"), # None if deleted
            doc_data["text_content"],
            doc_data["ocr_method"],
            doc_data.get("url"),
            doc_data.get("publication_date"),
            doc_data.get("doc_type", "generico")
        )
        
        # 1. Insert into main table
        async with self._sqlite_connection.execute(query, params) as cursor:
            pass # Transaction managed at connection level? aiosqlite usually commits on connection.commit()
            
        # 2. Insert into FTS (separate execute to avoid cursor mixup)
        if doc_data.get("text_content"):
            await self._sqlite_connection.execute(
                "INSERT INTO documents_fts (id, text_content, filename, source) VALUES (?, ?, ?, ?)",
                (doc_id, doc_data["text_content"], doc_data["filename"], doc_data["source"])
            )
        
        await self._sqlite_connection.commit()
        return doc_id
            
    async def search_documents_keyword(self, query_text: str, limit: int = 5) -> list[dict]:
        """
        BM25-like search using SQLite FTS5.
        """
        if not self._sqlite_connection:
            await self.get_sqlite()
            
        # Parametrized query for FTS is slightly tricky in SQLite, usually requires substitution or specific syntax
        # FTS5 query syntax: match 'phrase'
        # Safety: We should sanitize input slightly to prevent FTS syntax errors (like unmatched quotes)
        safe_query = query_text.replace("'", "''").replace('"', '""')
        
        # Simple match query
        sql = f"""
        SELECT id, text_content, filename, source, rank 
        FROM documents_fts 
        WHERE documents_fts MATCH ? 
        ORDER BY rank 
        LIMIT ?
        """
        
        try:
            async with self._sqlite_connection.execute(sql, (safe_query, limit)) as cursor:
                rows = await cursor.fetchall()
                results = []
                for row in rows:
                    # Map to compatible format with vector search result
                    results.append({
                        "content": row["text_content"], # This returns FULL content, might be heavy. FTS supports snippets.
                        # For Reranking, full content is okay if we chunk it later, but our documents_fts has full doc?
                        # ACTUALLY: FTS on full documents is bad for retrieval context.
                        # We usually want chunks.
                        # BUT: The requirement mimics keyword search on LEGISLATION (e.g. "Lei 8666").
                        # Finding the document is good.
                        "metadata": {
                            "filename": row["filename"],
                            "source": row["source"],
                            "doc_id": row["id"]
                        },
                        "score": 0.5 # Placeholder score for keyword match
                    })
                return results
        except Exception as e:
            logger.warning(f"FTS search failed (possibly invalid syntax): {e}")
            return []
    async def index_pre_chunked_data(self, doc_id: str, chunks: List[Dict], base_metadata: dict):
        """
        Indexes pre-calculated chunks (e.g. from HtmlLawIngestor) directly into ChromaDB.
        """
        collection = self.chroma_client.get_or_create_collection("sentinela_documents")
            
        ids = []
        documents = []
        metadatas = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_chunk_{i}"
            
            # Merit metadata
            meta = base_metadata.copy()
            meta.update(chunk.get("metadata", {}))
            meta["original_doc_id"] = doc_id # Consolidated key for inspector
            meta["chunk_index"] = i
            
            ids.append(chunk_id)
            documents.append(chunk["text"])
            metadatas.append(meta)
            
        if ids:
            collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            logger.info(f"Indexed {len(ids)} structured chunks for {doc_id}")

    async def index_document_text(self, doc_id: str, text: str, metadata: dict):
        """
        Standard indexing for raw text (OCR or plain text).
        Splits text into chunks and saves to ChromaDB.
        """
        if not text:
            return

        from src.utils.text_processing import text_splitter
        
        # Determine strategy based on source or explicitly if we had doc_type in metadata
        # Mappings: 
        # official_gazette -> diario_oficial
        # legislation -> legislation (if we had this source, for now logic defaults)
        
        doc_type = "general"
        source = metadata.get("source", "")
        filename = metadata.get("filename", "").lower()
        meta_doc_type = metadata.get("doc_type", "")
        
        if source == "official_gazette":
            doc_type = "diario_oficial"
        elif meta_doc_type == "lei" or "lei" in filename or "decreto" in filename:
             doc_type = "legislation"
        elif meta_doc_type: # Trust other types
             doc_type = meta_doc_type
            
        # 2. Split (Without Header, as requested)
        logger.info(f"🔍 Fragmentando texto em blocos para indexação...")
        chunks = text_splitter.split(text, doc_type=doc_type, context_prefix="")
        
        if not chunks:
            logger.warning("⚠️ Nenhum chunk gerado após fragmentação.")
            return

        collection = self.chroma_client.get_or_create_collection("sentinela_documents")
        
        # Batch processing (50 chunks per batch to prevent timeouts)
        batch_size = 50
        total_chunks = len(chunks)
        
        logger.info(f"🧠 Iniciando indexação vetorial: {total_chunks} fragmentos detectados.")
        
        for i in range(0, total_chunks, batch_size):
            end_idx = min(i + batch_size, total_chunks)
            batch_chunks = chunks[i:end_idx]
            
            # Generate IDs for this batch
            batch_ids = [f"{doc_id}_{k}" for k in range(i, end_idx)]
            
            # Generate Metadata for this batch
            batch_metadatas = []
            for k in range(i, end_idx):
                meta = metadata.copy()
                meta["chunk_index"] = k
                meta["total_chunks"] = total_chunks
                meta["original_doc_id"] = doc_id # Fix for deletion lookup later
                batch_metadatas.append(meta)
            
            try:
                collection.add(
                    documents=batch_chunks,
                    metadatas=batch_metadatas,
                    ids=batch_ids
                )
                logger.info(f"📊 Progresso de indexação: Lote {i//batch_size + 1}/{(total_chunks + batch_size - 1)//batch_size} ({end_idx}/{total_chunks}) salvo.")
            except Exception as e:
                logger.error(f"Indexing batch failed at index {i}: {e}")
                
        logger.info(f"Indexing complete for doc {doc_id}.")

    async def inspect_document(self, doc_id: str) -> Dict[str, Any]:
        """
        Retrieve all chunks and metadata for a specific document from Chroma.
        Useful for debugging text extraction quality.
        """
        try:
            collection = self.chroma_client.get_collection("sentinela_documents")
            # Fetch by ID prefix (since chunks are doc_id_0, doc_id_1...)
            # Chroma doesn't support prefix search on IDs easily, but we metadata filter is better.
            results = collection.get(
                where={"original_doc_id": doc_id},
                include=["documents", "metadatas"]
            )
            
            if not results["ids"]:
                # Fallback for old documents (id_prefix match)
                # This is expensive but necessary if metadata wasn't set on old docs
                return {"error": "No chunks found with metadata match."}

            # Sort by chunk_index to ensure logical order in UI
            combined = sorted(
                zip(results["documents"], results["metadatas"]),
                key=lambda x: x[1].get("chunk_index") if x[1].get("chunk_index") is not None else -1
            )

            return {
                "doc_id": doc_id,
                "total_chunks": len(results["ids"]),
                "chunks": [
                    {
                        "chunk_index": m.get("chunk_index"),
                        "content": d, # Return full content for deep inspection
                        "full_length": len(d),
                        "metadata": m
                    }
                    for d, m in combined
                ]
            }
        except Exception as e:
            logger.error(f"Inspect document failed: {e}")
            return {"error": str(e)}

    async def search_documents(self, query: str, limit: int = 5) -> list[dict]:
        """
        Semantic search for RAG context.
        """
        collection = self.chroma_client.get_or_create_collection("sentinela_documents")
        
        results = collection.query(
            query_texts=[query],
            n_results=limit
        )
        
        # Format results
        # Chroma returns lists of lists (one per query)
        if not results or not results["documents"]:
            return []
            
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        distances = results["distances"][0] if "distances" in results else [0]*len(docs)
        
        structured_results = []
        for doc, meta, dist in zip(docs, metas, distances):
            structured_results.append({
                "content": doc,
                "metadata": meta,
                "score": 1 - dist # Approx similarity if using cosine distance
            })
            
        return structured_results

    async def get_all_documents(self, limit: int = 50, offset: int = 0) -> list[dict]:
        """
        Lists documents from SQLite (metadata only).
        """
        if not self._sqlite_connection:
            await self.get_sqlite()
            
        query = "SELECT * FROM documents ORDER BY created_at DESC LIMIT ? OFFSET ?"
        async with self._sqlite_connection.execute(query, (limit, offset)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
            
    async def delete_document(self, doc_id: str) -> bool:
        """
        Deletes document from SQLite and VectorDB.
        """
        if not self._sqlite_connection:
            await self.get_sqlite()
            
        # 1. Delete from SQLite
        async with self._sqlite_connection.execute("DELETE FROM documents WHERE id = ?", (doc_id,)) as cursor:
            if cursor.rowcount == 0:
                logger.warning(f"Document {doc_id} not found in SQLite.")
                # We typically rely on SQLite ID, but let's check Chroma too just in case?
                # Actually, if it's not in SQLite, it might not exist or ID is wrong.
                
        # 2. Delete from ChromaDB
        # We need to find all chunks with this doc_id.
        # Our Indexing strategy uses IDs: f"{doc_id}_{i}"
        # But Chroma 'where' filter is better. 
        # Wait, we didn't store 'doc_id' in metadata explicitly in index_document_text?
        # Let's check `index_document_text`.
        # Metadatas are copies of `metadata` arg.
        # We should ensure `doc_id` is in metadata for easy deletion!
        # CURRENTLY: It is NOT guaranteed.
        # FIX: We will delete by ID prefix matching usually, BUT Chroma delete supports `where` metadata filter.
        # Since we might have missed adding doc_id to metadata in previous code, 
        # we will rely on ID matching logic or we must update index_document_text.
        # For now, let's try to delete by ID prefix if possible? 
        # Chroma `delete` accepts `ids` list. We don't know the list.
        # It accepts `where` filter.
        # If we didn't save doc_id in metadata, we have a problem.
        # Workaround: We know the ids are constructed as f"{doc_id}_{i}".
        # But we don't know how many chunks (i).
        # We can 'get' first to find them? Or just try deleting by filter if we had it.
        # Lesson: Always put doc_id in metadata.
        # Let's assume we implement metadata repair or just Try to use `where={"filename": ...}`? Unreliable.
        # Let's clean up best effort by assuming 0..1000 chunks? Hacky.
        # PROPER FIX: Chroma `delete` with `where_document` content? No.
        # `delete` allows `ids`.
        # Let's update `index_document_text` in general for future. 
        # But for `delete_document` right now:
        # We will attempt to delete chunks by guessing `doc_id` in metadata isn't there.
        # Actually, in `index_document_text` we wrote: `ids = [f"{doc_id}_{i}" ...]`.
        # We can query generic metadata to find them?
        # For this iteration, let's assume we can't easily delete from Chroma without ID in metadata OR knowing all IDs.
        # I'll implement a 'get' loop to find IDs starting with.
        
        collection = self.chroma_client.get_or_create_collection("sentinela_documents")
        
        # Deleta usando o filtro de metadados original_doc_id (mais robusto)
        try:
            collection.delete(where={"original_doc_id": doc_id})
            logger.info(f"Todos os vetores do documento {doc_id} foram removidos do ChromaDB.")
        except Exception as e:
            logger.error(f"Erro ao deletar vetores do ChromaDB: {e}")
            # Tentativa de fallback por prefixo de ID (caso o metadado tenha falhado no passado)
            # Como não sabemos o total, tentamos um range maior, mas o 'where' é o oficial agora.
            potential_ids = [f"{doc_id}_{i}" for i in range(2000)]
            collection.delete(ids=potential_ids)
            potential_ids_chunk = [f"{doc_id}_chunk_{i}" for i in range(2000)]
            collection.delete(ids=potential_ids_chunk)
        
        return True

    async def close(self):
        """
        Closes connections.
        """
        if self._sqlite_connection:
            await self._sqlite_connection.close()
            self._sqlite_connection = None

db_manager = DatabaseManager()
