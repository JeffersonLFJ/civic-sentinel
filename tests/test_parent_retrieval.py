
import asyncio
import logging
import sys
import os

# Add src to path
sys.path.append(os.getcwd())

from src.core.database import db_manager

# Configure simple logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_parent_retrieval_flow():
    print("\n🚀 Starting Parent Retrieval Verification Test...")
    
    # 1. Setup Dummy Doc
    doc_id = "test_doc_parent_v1"
    # A text mimicking a PDF with 2 pages
    text_content = (
        "SENTINELA RELATÓRIO PÁGINA 1\n"
        "Este é o conteúdo da primeira página sobre Segurança.\n"
        "A segurança pública é prioridade.\n"
        "\f\n" # Form Feed Marker
        "SENTINELA RELATÓRIO PÁGINA 2\n"
        "Este é o conteúdo da segunda página sobre Saúde.\n"
        "A saúde pública é vital.\n"
    )
    
    metadata = {
        "filename": "relatorio_teste.pdf",
        "source": "test_script",
        "doc_type": "general" # Should trigger Page splitting
    }
    
    # 2. Ingest
    print("\n[Action] Indexing Document...")
    try:
        await db_manager.index_document_text(doc_id, text_content, metadata)
        print("✅ Indexing call completed.")
    except Exception as e:
        print(f"❌ Indexing failed: {e}")
        return

    # 3. Verify SQLite Parents
    print("\n[Verification] Checking 'doc_parents' table in SQLite...")
    conn = await db_manager.get_sqlite()
    try:
        async with conn.execute("SELECT * FROM doc_parents WHERE doc_id = ?", (doc_id,)) as cursor:
            rows = await cursor.fetchall()
            print(f"📊 Found {len(rows)} parent chunks.")
            
            if len(rows) == 2:
                print("✅ Correct number of Parents (Pages).")
                p1 = dict(rows[0])
                print(f"   Parent 1 ID: {p1['id']}")
                print(f"   Parent 1 Type: {p1['parent_type']}")
                print(f"   Parent 1 Content Snippet: {p1['text_content'][:40]}...")
                
                p1_id = p1['id']
                # 4. Check retrieval by ID
                retrieved = await db_manager.get_parent_content(p1_id)
                if retrieved == p1['text_content']:
                     print("✅ get_parent_content works perfectly.")
                else:
                     print("❌ get_parent_content returned mismatch/None.")
            else:
                print(f"❌ Expected 2 parents, found {len(rows)}.")
    except Exception as e:
        print(f"❌ SQLite Check Failed: {e}")

    # 5. Verify Chroma Metadata
    print("\n[Verification] Checking ChromaDB Metadata...")
    try:
        collection = db_manager.chroma_client.get_collection("sentinela_documents")
        results = collection.get(where={"original_doc_id": doc_id})
        
        if results and results['ids']:
            print(f"✅ Found {len(results['ids'])} micro chunks in Chroma.")
            first_meta = results['metadatas'][0]
            print(f"   Sample Metadata: {first_meta}")
            
            if "parent_id" in first_meta:
                print(f"✅ 'parent_id' present in metadata: {first_meta['parent_id']}")
                
                # Check link
                parent_id_chroma = first_meta['parent_id']
                content_check = await db_manager.get_parent_content(parent_id_chroma)
                if content_check:
                    print("✅ Link confirmed: Chroma Metadata -> SQLite Parent Content.")
                else:
                    print("❌ Broken Link: Chroma parent_id not found in SQLite.")
            else:
                print("❌ 'parent_id' MISSING in metadata.")
        else:
            print("❌ No chunks found in Chroma.")
            
    except Exception as e:
        print(f"❌ Chroma Verification Failed: {e}")
    
    # Cleanup
    # await db_manager.delete_document(doc_id) # Optional

    await db_manager.close()

if __name__ == "__main__":
    asyncio.run(test_parent_retrieval_flow())
