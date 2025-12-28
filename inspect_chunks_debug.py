import chromadb
from src.config import settings
import json

def inspect_chunks(doc_id):
    client = chromadb.PersistentClient(path=str(settings.CHROMADB_DIR))
    collection = client.get_collection("sentinela_documents")
    
    results = collection.get(
        where={"original_doc_id": doc_id},
        include=["documents", "metadatas"]
    )
    
    if not results['ids']:
        print("Nenhum chunk encontrado.")
        return

    # Organiza por index
    combined = []
    for doc, meta in zip(results['documents'], results['metadatas']):
        combined.append((meta.get('chunk_index', 0), doc, meta))
    
    combined.sort(key=lambda x: x[0])
    
    print(f"Total de Chunks: {len(combined)}")
    print("-" * 40)
    
    for idx, text, meta in combined[:5]: # Mostrar apenas os 5 primeiros
        print(f"[{idx}] (Tipo: {meta.get('doc_type', 'N/A')})")
        print(f"Texto ({len(text)} chars): {text[:200]}...")
        print("-" * 20)

if __name__ == "__main__":
    inspect_chunks("9317755a-3c4d-4a04-a41a-adeade66f526")
