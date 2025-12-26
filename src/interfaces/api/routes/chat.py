from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from src.core.llm_client import llm_client
from src.utils.security import anonymize_user

router = APIRouter()

class Message(BaseModel):
    role: str # 'user' or 'assistant'
    content: str

class ChatRequest(BaseModel):
    message: str
    user_id: str
    history: Optional[List[Message]] = None
    images: Optional[List[str]] = None

@router.post("/")
async def chat_endpoint(request: ChatRequest):
    """
    Conversational endpoint with RAG and Memory.
    """
    user_hash = anonymize_user(request.user_id)
    
    try:
        from src.core.database import db_manager
        
        # 1. Retrieve Context
        context_docs = []
        if len(request.message) > 5:
            context_docs = await db_manager.search_documents(request.message, limit=3)
            
        # 2. Build Context String for SYSTEM
        context_str = ""
        citation_metadata = []
        
        if context_docs:
            context_str = "CONTEXTO DE DOCUMENTOS OFICIAIS RECUPERADO:\n"
            for i, doc in enumerate(context_docs):
                meta = doc["metadata"]
                source_info = f"Fonte: {meta.get('filename')} ({meta.get('source')})"
                context_str += f"\n[Documento {i+1}] {source_info}\nConteúdo: {doc['content']}\n"
                citation_metadata.append(meta)
            context_str += "\nUse o contexto acima para fundamentar sua resposta. Se não souber, diga que não encontrou nos documentos.\n"
        
        # 3. Assemble Full Prompt with History
        # We'll use a chatML-like format or simple turn blocks for Gemma 2/3
        full_conversation = ""
        if context_str:
            full_conversation += f"SISTEMA: {context_str}\n"
            
        if request.history:
            for msg in request.history:
                role = "USUÁRIO" if msg.role == "user" else "ASSISTENTE"
                full_conversation += f"{role}: {msg.content}\n"
        
        # Current message
        full_conversation += f"USUÁRIO: {request.message}\nASSISTENTE: "
        
        # 4. Log Audit
        citation_names = ", ".join([m.get("filename", "unknown") for m in citation_metadata])
        await db_manager.log_audit(
            action="chat_rag",
            details=f"Query: {request.message[:50]}... | Citations: {citation_names}",
            user_hash=user_hash,
            confidence_score=0.9 # Default for gemma responses with context
        )
        
        return {
            "response": response["content"],
            "metadata": {
                "model": response["model"],
                "timestamp": response["timestamp"],
                "citations": citation_metadata
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
