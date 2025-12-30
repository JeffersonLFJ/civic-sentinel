
import asyncio
import sys
import os
import logging
import uuid 

# Add src to path
sys.path.append(os.getcwd())

from src.core.database import db_manager

# Configure logger
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

async def test_refinement():
    print("\n🏗️ Starting Refinement Verification Test...")
    
    doc_id = f"test_doc_refinement_{uuid.uuid4().hex[:8]}"
    
    # 1. Setup multi-page Doc
    text_content = (
        "SENTINELA RELATÓRIO PÁGINA 1\n"
        "Esta é a primeira pagina.\n"
        "A frase importante começa aqui e termina na... \n" # Sentence cut
        "\f"
        "SENTINELA RELATÓRIO PÁGINA 2\n"
        "próxima página. Esta é a continuação.\n"
    )
    
    metadata = {
        "filename": "refinement_test.pdf",
        "source": "test_script",
        "doc_type": "general"
    }

    # 2. Ingest
    print(f"\n[Action] Indexing {doc_id}...")
    try:
        # Use manager method to avoid locking/transaction retention issues
        doc_data = {
             "filename": metadata["filename"],
             "source": metadata["source"],
             "text_content": text_content,
             "ocr_method": "test",
             "doc_type": metadata["doc_type"]
        }
        
        # NOTE: save_document_record returns a NEW UUID. We capture it.
        real_doc_id = await db_manager.save_document_record(doc_data)
        doc_id = real_doc_id 
        print(f"   [Info] Real Doc ID generated: {doc_id}")
        
        await db_manager.index_document_text(doc_id, text_content, metadata)
        print("✅ Indexing successful.")
    except Exception as e:
        print(f"❌ Indexing failed: {e}")
        return

    # 3. Verify Page Peeking
    print("\n[Verification] Testing Page Peeking...")
    conn = await db_manager.get_sqlite()
    try:
        # Get Parent 0 ID
        p0_id = f"{doc_id}_parent_0"
        content = await db_manager.get_parent_content(p0_id)
        
        if content:
            print(f"   Original Content Length: {len('SENTINELA RELATÓRIO PÁGINA 1... na... ')}")
            print(f"   Retrieved Content Length: {len(content)}")
            
            if "Continua na Próxima Página" in content:
                print("✅ Peek Marker found.")
                if "próxima página" in content:
                    print("✅ Next page content successfully peeked.")
                else:
                    print("❌ Marker found but content missing.")
            else:
                print("❌ Peeking failed: No marker found.")
                print(f"   Content snippet: {content[-50:]}")
        else:
            print("❌ Parent 0 not found.")
            
    except Exception as e:
        print(f"❌ Peeking Test Failed: {e}")

    # 4. Verify Atomic Deletion
    print("\n[Verification] Testing Atomic Deletion...")
    try:
        # Check FTS before delete
        async with conn.execute("SELECT count(*) FROM documents_fts WHERE id = ?", (doc_id,)) as c:
            count = (await c.fetchone())[0]
            print(f"   FTS Count before delete: {count}")
            
        success = await db_manager.delete_document(doc_id)
        if success:
            print("✅ Delete command executed.")
            
            # Check SQLite
            async with conn.execute("SELECT count(*) FROM documents WHERE id = ?", (doc_id,)) as c:
                count_main = (await c.fetchone())[0]
                
            async with conn.execute("SELECT count(*) FROM doc_parents WHERE doc_id = ?", (doc_id,)) as c:
                count_parents = (await c.fetchone())[0]
                
            async with conn.execute("SELECT count(*) FROM documents_fts WHERE id = ?", (doc_id,)) as c:
                count_fts = (await c.fetchone())[0]
                
            if count_main == 0 and count_parents == 0 and count_fts == 0:
                 print("✅ SQLite Clean (Main, Parents, FTS).")
            else:
                 print(f"❌ SQLite Dirty: Main={count_main}, Parents={count_parents}, FTS={count_fts}")
                 
            # Check Chroma
            collection = db_manager.chroma_client.get_collection("sentinela_documents")
            results = collection.get(where={"original_doc_id": doc_id})
            if len(results['ids']) == 0:
                print("✅ ChromaDB Clean.")
            else:
                 print(f"❌ ChromaDB Dirty: Found {len(results['ids'])} chunks.")
                 
        else:
            print("❌ Delete command returned False.")
            
    except Exception as e:
         print(f"❌ Deletion Test Failed: {e}")

    await db_manager.close()

if __name__ == "__main__":
    asyncio.run(test_refinement())
