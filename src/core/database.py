import chromadb
from chromadb.config import Settings as ChromaSettings
import aiosqlite
import logging
from typing import Dict, Any, List, Optional
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
            
            # Optimization: Enable WAL mode for better concurrency
            await self._sqlite_connection.execute("PRAGMA journal_mode=WAL")
            
            # Enforce Foreign Keys
            await self._sqlite_connection.execute("PRAGMA foreign_keys = ON")
            
            # Initialize schema if needed
            await self._init_sqlite_schema()
            
        return self._sqlite_connection

    # ... (skipping unchanged _init_sqlite_schema codes) ...

    async def delete_document(self, doc_id: str) -> bool:
        """
        Deletes document from SQLite and VectorDB atomically.
        """
        if not self._sqlite_connection:
            await self.get_sqlite()
            
        try:
            # 1. Delete from SQLite (Transactions)
            async with self._sqlite_connection.cursor() as cursor:
                # Delete from FTS first (Virtual table)
                await cursor.execute("DELETE FROM documents_fts WHERE id = ?", (doc_id,))
                
                # Delete from Main Table
                # With PRAGMA foreign_keys = ON, this SHOULD cascade to doc_parents.
                # But let's be paranoid and explicit for robustness.
                await cursor.execute("DELETE FROM doc_parents WHERE doc_id = ?", (doc_id,))
                await cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
                
                deleted_count = cursor.rowcount
            
            await self._sqlite_connection.commit()
            
            if deleted_count == 0:
                logger.warning(f"Document {doc_id} not found in SQLite to delete.")
            
            # 2. Delete from ChromaDB
            collection = self.chroma_client.get_or_create_collection("sentinela_documents")
            try:
                collection.delete(where={"original_doc_id": doc_id})
                logger.info(f"Vectors for {doc_id} deleted from ChromaDB.")
            except Exception as e:
                logger.error(f"Chroma metadata delete failed: {e}. Trying ID fallback.")
                # Fallback range delete
                potential_ids = [f"{doc_id}_micro_{i}" for i in range(2000)]
                collection.delete(ids=potential_ids)
                
            return True
            
        except Exception as e:
            logger.error(f"Atomic Delete failed for {doc_id}: {e}")
            return False

    async def close(self):
        """
        Closes connections.
        """
        if self._sqlite_connection: 
            await self._sqlite_connection.close()
            self._sqlite_connection = None

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
            doc_type TEXT DEFAULT 'generico', -- 'lei', 'diario_oficial', 'tabela'
            sphere TEXT DEFAULT 'unknown', -- 'federal', 'estadual', 'municipal'
            status TEXT DEFAULT 'active', -- 'active' or 'pending' (staging)
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """

        query_parents = """
        CREATE TABLE IF NOT EXISTS doc_parents (
            id TEXT PRIMARY KEY, -- doc_id + "_" + parent_index
            doc_id TEXT NOT NULL,
            text_content TEXT NOT NULL,
            parent_type TEXT, -- 'page', 'article', 'act', 'table_page'
            parent_index INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(doc_id) REFERENCES documents(id) ON DELETE CASCADE
        );
        """
        
        async with self._sqlite_connection.cursor() as cursor:
            await cursor.execute(query_audit)
            await cursor.execute(query_users)
            await cursor.execute(query_docs)
            await cursor.execute(query_parents)
            
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
            
            # Standard migrations (Alembick-less)
            migrations = [
                ("ALTER TABLE documents ADD COLUMN url TEXT", "url"),
                ("ALTER TABLE documents ADD COLUMN publication_date DATE", "publication_date"),
                ("ALTER TABLE documents ADD COLUMN doc_type TEXT DEFAULT 'generico'", "doc_type"),
                ("ALTER TABLE documents ADD COLUMN sphere TEXT DEFAULT 'unknown'", "sphere"),
                ("ALTER TABLE documents ADD COLUMN status TEXT DEFAULT 'active'", "status"),
                ("ALTER TABLE audit_logs ADD COLUMN query TEXT", "query"),
                ("ALTER TABLE audit_logs ADD COLUMN response TEXT", "response"),
                ("ALTER TABLE audit_logs ADD COLUMN sources_json TEXT", "sources_json")
            ]
            
            for m_sql, col_name in migrations:
                try:
                    await cursor.execute(m_sql)
                except Exception:
                    pass # Column exists or table newly created
            
            # Drop obsolete column
            try:
                await cursor.execute("ALTER TABLE documents DROP COLUMN urgency_level")
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
        doc_id = doc_data.get("id") or str(uuid.uuid4())
        
        query = """
        INSERT INTO documents (
            id, filename, source, storage_path, text_content, ocr_method, url, publication_date, doc_type, sphere, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            doc_id,
            doc_data["filename"],
            doc_data["source"],
            doc_data.get("storage_path"), 
            doc_data["text_content"],
            doc_data.get("ocr_method", "manual"),
            doc_data.get("url"),
            doc_data.get("publication_date"),
            doc_data.get("doc_type", "generico"),
            doc_data.get("sphere", "unknown"),
            doc_data.get("status", "active")
        )
        
        async with self._sqlite_connection.execute(query, params) as cursor:
            pass 
            
        if doc_data.get("text_content"):
            await self._sqlite_connection.execute(
                "INSERT INTO documents_fts (id, text_content, filename, source) VALUES (?, ?, ?, ?)",
                (doc_id, doc_data["text_content"], doc_data["filename"], doc_data["source"])
            )
        
        await self._sqlite_connection.commit()
        return doc_id
            
    async def search_documents_keyword(self, query_text: str, limit: int = 5, sphere: str = None) -> list[dict]:
        """
        BM25-like search using SQLite FTS5.
        """
        if not self._sqlite_connection:
            await self.get_sqlite()
            
        safe_query = query_text.replace("'", "''").replace('"', '""')
        
        # Se houver esfera, filtramos cruzando com a tabela principal
        sql = f"""
        SELECT f.id, f.text_content, f.filename, f.source, f.rank, d.sphere, d.publication_date, d.doc_type
        FROM documents_fts f
        JOIN documents d ON f.id = d.id
        WHERE f.text_content MATCH ? 
        AND d.status = 'active'
        """
        
        params = [safe_query]
        if sphere:
            sql += " AND d.sphere = ?"
            params.append(sphere)
            
        sql += " ORDER BY f.rank LIMIT ?"
        params.append(limit)
        
        try:
            async with self._sqlite_connection.execute(sql, params) as cursor:
                rows = await cursor.fetchall()
                results = []
                for row in rows:
                    results.append({
                        "content": row["text_content"],
                        "metadata": {
                            "filename": row["filename"],
                            "source": row["source"],
                            "doc_id": row["id"],
                            "sphere": row["sphere"],
                            "publication_date": row["publication_date"],
                            "doc_type": row["doc_type"]
                        },
                        "score": 0.5 
                    })
                return results
        except Exception as e:
            logger.warning(f"FTS search failed (possibly invalid syntax): {e}")
            return []
    async def index_pre_chunked_data(self, doc_id: str, chunks: List[Dict], base_metadata: dict):
        """
        Indexes pre-calculated chunks (e.g. from HtmlLawIngestor or TableSplitter).
        TREATED AS MACRO CHUNKS (Parents).
        1. Save 'chunk' as Parent.
        2. Split 'chunk' into Micros -> Chroma.
        """
        from src.utils.text_processing import text_splitter
        
        collection = self.chroma_client.get_or_create_collection("sentinela_documents")
            
        ids = []
        documents = []
        metadatas = []
        
        total_parents = len(chunks)
        total_micros = 0
        
        doc_type = base_metadata.get("doc_type", "general")
        parent_type = "generic_macro"
        if doc_type == "tabela":
             parent_type = "table_page"
        elif doc_type == "lei" or doc_type == "legislation":
             parent_type = "article"
        
        for p_idx, chunk in enumerate(chunks):
            # A. Save Parent
            parent_text = chunk["text"]
            # Save parent_chunk expects (doc_id, index, text, type)
            parent_id = await self.save_parent_chunk(doc_id, p_idx, parent_text, parent_type)
            
            # B. Split Micro
            micro_chunks = []
            if doc_type == "tabela":
                # Split 50-row MD table into 5-row MD tables
                micro_chunks = text_splitter.split_markdown_table(parent_text, chunk_rows=5)
            elif doc_type == "legislation" or doc_type == "lei":
                # Split Article into Paragraphs
                micro_chunks = text_splitter.split_by_paragraphs(parent_text)
            else:
                # Default fallback (should not happen often for pre-chunked unless manual)
                micro_chunks = text_splitter.split_semantically(parent_text)
                
            if not micro_chunks:
                 micro_chunks = [parent_text]

            # C. Accumulate Micros
            for m_idx, m_text in enumerate(micro_chunks):
                chunk_id = f"{parent_id}_micro_{m_idx}"
                
                # Merit metadata
                meta = base_metadata.copy()
                meta.update(chunk.get("metadata", {})) # Specific chunk metadata
                meta["original_doc_id"] = doc_id
                meta["parent_id"] = parent_id
                meta["parent_index"] = p_idx
                meta["chunk_index"] = m_idx 
                meta["parent_type"] = parent_type
                
                ids.append(chunk_id)
                documents.append(m_text)
                metadatas.append(meta)
            
        if ids:
            try:
                collection.add(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas
                )
                logger.info(f"Indexed {len(ids)} micro chunks (from {total_parents} parents) for {doc_id}")
            except Exception as e:
                logger.error(f"Failed to index structured micros: {e}")

    async def index_document_text(self, doc_id: str, text: str, metadata: dict):
        """
        Standard indexing for raw text (OCR or plain text) with Parent Retrieval.
        1. Splits into MACRO chunks (Parents) -> SQLite.
        2. Splits MACRO into MICRO chunks (Children) -> ChromaDB.
        """
        if not text:
            return

        from src.utils.text_processing import text_splitter
        
        doc_type = "general"
        source = metadata.get("source", "")
        filename = metadata.get("filename", "").lower()
        meta_doc_type = metadata.get("doc_type", "")
        
        if source == "official_gazette" or meta_doc_type == "diario_oficial" or "diario" in filename:
            doc_type = "diario_oficial"
        elif meta_doc_type == "lei" or "lei" in filename or "decreto" in filename:
             doc_type = "legislation"
        elif meta_doc_type:
             doc_type = meta_doc_type
             
        # 1. Macro Splitting (Defining Parents)
        logger.info(f"🔍 Fragmentando MACRO chunks para {doc_id} (Tipo: {doc_type})...")
        macro_chunks = []
        
        if doc_type == "legislation":
            # Uses regex for Articles
            macro_chunks = text_splitter.split_by_law_articles(text)
            parent_type = "article"
        elif doc_type == "diario_oficial":
            # Uses regex for Acts
            macro_chunks = text_splitter.split_legal_acts(text)
            parent_type = "act"
        else:
            # General / PDF -> Physical Pages
            # We assume text has \f markers if from our optimized OCR
            macro_chunks = text_splitter.split_pages(text)
            parent_type = "page"

        if not macro_chunks:
            logger.warning("⚠️ Nenhum Macro-Chunk gerado. Tratando texto inteiro como único pai.")
            macro_chunks = [text]

        collection = self.chroma_client.get_or_create_collection("sentinela_documents")
        
        total_parents = len(macro_chunks)
        total_micros_indexed = 0
        
        # 2. Process Each Parent
        for p_idx, parent_text in enumerate(macro_chunks):
            # A. Save Parent to SQLite
            parent_id = await self.save_parent_chunk(doc_id, p_idx, parent_text, parent_type)
            
            # B. Split into Micros (Children)
            # Strategy: Semantic Split for General, Paragraphs for others?
            # User requirement: "General Docs -> Semantic Splitter". Rules don't forbid semantic for others.
            # But "Table" has specific rules. (Table logic is separate in upload.py for now).
            # For Legislation, semantic might be overkill if paragraphs are clear, but helpful.
            # Let's use Semantic for General/Diario and Paragraphs for Law (structure is strict).
            
            micro_chunks = []
            if doc_type == "general":
                 micro_chunks = text_splitter.split_semantically(parent_text)
            else:
                 # Legislation/Diario usually structured by paragraphs
                 micro_chunks = text_splitter.split_by_paragraphs(parent_text)
            
            if not micro_chunks:
                continue

            # C. Index Micros to Chroma
            ids = []
            docs = []
            metas = []
            
            for m_idx, m_text in enumerate(micro_chunks):
                chunk_id = f"{parent_id}_micro_{m_idx}"
                
                # Metadata inheritance
                meta = metadata.copy()
                meta["chunk_index"] = m_idx # Relative to parent? Or Global?
                # Global index is hard to track without counter. Let's strictly use Parent ref.
                meta["parent_id"] = parent_id
                meta["original_doc_id"] = doc_id
                meta["parent_index"] = p_idx
                meta["parent_type"] = parent_type
                
                ids.append(chunk_id)
                docs.append(m_text)
                metas.append(meta)
            
            if ids:
                try:
                    collection.add(ids=ids, documents=docs, metadatas=metas)
                    total_micros_indexed += len(ids)
                except Exception as e:
                    logger.error(f"Failed to index micros for parent {parent_id}: {e}")

        logger.info(f"Indexing complete for {doc_id}. Parents: {total_parents}, Micros: {total_micros_indexed}.")

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

    async def get_pending_documents(self) -> List[Dict[str, Any]]:
        """
        Returns all documents in 'pending' status for the Staging Area.
        """
        if not self._sqlite_connection:
            await self.get_sqlite()
            
        query = "SELECT id, filename, source, doc_type, sphere, publication_date, created_at FROM documents WHERE status = 'pending' ORDER BY created_at DESC"
        async with self._sqlite_connection.execute(query) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def update_document_metadata(self, doc_id: str, updates: Dict[str, Any]):
        """
        Updates document metadata (doc_type, sphere, publication_date) in SQLite.
        """
        if not self._sqlite_connection:
            await self.get_sqlite()
            
        fields = []
        params = []
        for key, value in updates.items():
            if key in ["doc_type", "sphere", "publication_date"]:
                fields.append(f"{key} = ?")
                params.append(value)
        
        if not fields:
            return
            
        params.append(doc_id)
        query = f"UPDATE documents SET {', '.join(fields)} WHERE id = ?"
        
        async with self._sqlite_connection.execute(query, params) as cursor:
            pass
        await self._sqlite_connection.commit()

    async def activate_document(self, doc_id: str) -> bool:
        """
        Promotes a document from 'pending' to 'active' and indexes it in ChromaDB.
        """
        if not self._sqlite_connection:
            await self.get_sqlite()
            
        start_time = time.perf_counter()
        
        # Build Query String
        if isinstance(query, list):
            # Clean and join with OR
            clean_terms = [t.replace('"', '').replace("'", "") for t in query if t.strip()]
            if not clean_terms:
                return []
            # FTS5 syntax: term1 OR term2
            fts_query_str = " OR ".join([f'"{t}"' for t in clean_terms])
        else:
            # Legacy string fallback
            fts_query_str = f'"{query}"'

        # FTS5 Query
        # We match against the virtual table but join with real table for metadata
        
        # 2. Index in ChromaDB
        # We need final_meta_type logic usually, but here we use what's in the DB (already refined or corrected by user)
        base_meta = {
            "source": doc["source"], 
            "filename": doc["filename"], 
            "doc_type": doc["doc_type"],
            "sphere": doc["sphere"],
            "status": "active"
        }
        
        # Simple indexing (as in upload.py)
        await self.index_document_text(
            doc_id=doc_id, 
            text=doc["text_content"],
            metadata=base_meta
        )
        
        # 3. Update status to 'active'
        async with self._sqlite_connection.execute("UPDATE documents SET status = 'active' WHERE id = ?", (doc_id,)) as cursor:
            pass
        await self._sqlite_connection.commit()
        
        logger.info(f"✅ Documento {doc_id} ATIVADO e indexado com sucesso.")
        return True

    async def get_context_window(self, doc_id: str, center_index: int, window_size: int = 1) -> str:
        """
        Retrieves a 'window' of chunks around a specific index.
        Useful for expanding context without loading the full document.
        """
        try:
            collection = self.chroma_client.get_collection("sentinela_documents")
            
            # Range query in Chroma is tricky with where filter only supporting direct comparisons usually
            # But we can try multiple queries or a range filter if supported.
            # Using $gte and $lte on chunk_index
            
            start_idx = max(0, center_index - window_size)
            end_idx = center_index + window_size
            
            results = collection.get(
                where={
                    "$and": [
                        {"original_doc_id": doc_id},
                        {"chunk_index": {"$gte": start_idx}},
                        {"chunk_index": {"$lte": end_idx}}
                    ]
                },
                include=["documents", "metadatas"]
            )
            
            if not results["documents"]:
                return ""
            
            # Sort by index
            combined = sorted(
                zip(results["documents"], results["metadatas"]),
                key=lambda x: x[1].get("chunk_index", 0)
            )
            
            # Join texts
            full_text = "\n\n".join([d for d, m in combined])
            return full_text
            
        except Exception as e:
            logger.error(f"Context window retrieval failed: {e}")
            return ""

    async def search_documents(self, query: str, limit: int = 5, where: dict = None, sphere: str = None) -> list[dict]:
        """
        Semantic search for RAG context.
        """
        kwargs = {
            "query_texts": [query],
            "n_results": limit
        }
        
        # Default filter: Active only
        status_filter = {"status": "active"}
        
        if not where and not sphere:
            kwargs["where"] = status_filter
        else:
            # Combine filters using $and
            conditions = [status_filter]
            if where:
                conditions.append(where)
            if sphere:
                conditions.append({"sphere": sphere})
            
            kwargs["where"] = {"$and": conditions}
        
        collection = self.chroma_client.get_or_create_collection("sentinela_documents")
        results = collection.query(**kwargs)
        
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

    async def get_document_by_id(self, doc_id: str) -> Dict[str, Any]:
        """
        Fetches full document details by ID from SQLite.
        """
        if not self._sqlite_connection:
            await self.get_sqlite()
            
        query = "SELECT * FROM documents WHERE id = ?"
        async with self._sqlite_connection.execute(query, (doc_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None
            
    async def clear_vector_store(self) -> bool:
        """
        DANGER: Clears ALL vectors from ChromaDB.
        """
        try:
            # PersistentClient doesn't have a simple 'reset' method exposed easily on client?
            # client.reset() is only for in-memory or if ALLOW_RESET is set.
            # Safer to delete the collection and recreate.
            self.chroma_client.delete_collection("sentinela_documents")
            # Recreate empty
            self.chroma_client.get_or_create_collection("sentinela_documents")
            logger.warning("⚠️ Vector Store fully reset by admin request.")
            return True
        except Exception as e:
            logger.error(f"Failed to clear vector store: {e}")
            return False

    async def delete_document(self, doc_id: str) -> bool:
        """
        Deletes document from SQLite and VectorDB atomically.
        """
        if not self._sqlite_connection:
            await self.get_sqlite()
            
        try:
            # 1. Delete from SQLite (Transactions)
            # 'doc_parents' has ON DELETE CASCADE in definition, so it should auto-delete.
            # 'documents_fts' needs manual deletion because it's a virtual table without FK constraints usually.
            
            async with self._sqlite_connection.cursor() as cursor:
                # Delete from FTS first (using internal ID mapping if possible, or matches)
                # FTS delete is usually done by DELETE FROM table WHERE rowid = ... or matching cols.
                # Since our FTS id is UNINDEXED, simple delete by ID might be slow or unsupported if not rowid.
                # But we inserted 'id' as a column.
                await cursor.execute("DELETE FROM documents_fts WHERE id = ?", (doc_id,))
                
                # Delete from main table (Triggers Cascade for doc_parents)
                await cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
                
                deleted_count = cursor.rowcount
            
            await self._sqlite_connection.commit()
            
            if deleted_count == 0:
                logger.warning(f"Document {doc_id} not found in SQLite to delete.")
                # We still try to clean Chroma just in case phantom data exists
                
            # 2. Delete from ChromaDB
            # We now reliably save 'original_doc_id' in metadata.
            collection = self.chroma_client.get_or_create_collection("sentinela_documents")
            
            try:
                # Try delete by metadata (Best Modern Method)
                collection.delete(where={"original_doc_id": doc_id})
                logger.info(f"Vectors for {doc_id} deleted from ChromaDB.")
            except Exception as e:
                logger.error(f"Chroma metadata delete failed: {e}. Trying fallback.")
                # Fallback: Delete potential IDs if metadata failed
                potential_ids = [f"{doc_id}_micro_{i}" for i in range(5000)] # Adjusted naming convention
                collection.delete(ids=potential_ids)
                
            return True
            
        except Exception as e:
            logger.error(f"Atomic Delete failed for {doc_id}: {e}")
            return False

    async def save_parent_chunk(self, doc_id: str, parent_index: int, text: str, parent_type: str) -> str:
        """
        Saves a Macro Chunk (Parent) to SQLite.
        Returns the parent_id (doc_id + _parent_ + index).
        """
        if not self._sqlite_connection:
            await self.get_sqlite()
            
        parent_id = f"{doc_id}_parent_{parent_index}"
        
        # Insert or Replace to allow re-ingestion
        query = """
        INSERT OR REPLACE INTO doc_parents (id, doc_id, text_content, parent_type, parent_index)
        VALUES (?, ?, ?, ?, ?)
        """
        
        async with self._sqlite_connection.execute(query, (parent_id, doc_id, text, parent_type, parent_index)) as cursor:
            pass
            
        await self._sqlite_connection.commit()
        return parent_id

    async def get_parent_content(self, parent_id: str) -> Optional[str]:
        """
        Retrieves the full content of a Parent Chunk from SQLite.
        If type is 'page', peeks at the next page to fix cut sentences.
        """
        if not self._sqlite_connection:
            await self.get_sqlite()
            
        query = "SELECT id, doc_id, text_content, parent_type, parent_index FROM doc_parents WHERE id = ?"
        async with self._sqlite_connection.execute(query, (parent_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
                
            content = row["text_content"]
            parent_type = row["parent_type"]
            
            # PAGE PEEKING LOGIC
            # Only for PDFs/General pages where sentences might span boundaries
            if parent_type == "page":
                doc_id = row["doc_id"]
                current_index = row["parent_index"]
                next_index = current_index + 1
                
                # Fetch next page for peeking
                peek_query = "SELECT text_content FROM doc_parents WHERE doc_id = ? AND parent_index = ?"
                async with self._sqlite_connection.execute(peek_query, (doc_id, next_index)) as peek_cursor:
                    next_page = await peek_cursor.fetchone()
                    if next_page:
                        # Append first 200 chars (approx 2 sentences)
                        peek_text = next_page["text_content"][:250].replace("\n", " ") # Flatten slightly
                        content += f"\n\n[...Continua na Próxima Página]: {peek_text}..."
            
            return content

db_manager = DatabaseManager()
