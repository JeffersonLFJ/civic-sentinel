import sys
import os
import asyncio
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.config import settings
import chromadb

def inspect():
    db_path = "data/chromadb"
    print(f"Connecting to ChromaDB at {db_path}...")
    client = chromadb.PersistentClient(path=db_path)
    
    try:
        collection = client.get_collection("sentinela_documents")
        count = collection.count()
        print(f"Total chunks in collection: {count}")
        
        if count == 0:
            print("Collection is empty.")
            return

        # Get last 5 items
        print("\nLast 5 Chunks:")
        results = collection.get(limit=5, include=["metadatas", "documents"])
        
        for i in range(len(results["ids"])):
            doc_id = results["ids"][i]
            meta = results["metadatas"][i]
            content = results["documents"][i]
            
            print(f"\nID: {doc_id}")
            print(f"Metadata: {meta}")
            print(f"Content Length: {len(content)} characters")
            print(f"Content Preview: {content[:500]}...") # First 500 chars
            print("-" * 50)
            
    except Exception as e:
        print(f"Error accessing collection: {e}")

if __name__ == "__main__":
    inspect()
