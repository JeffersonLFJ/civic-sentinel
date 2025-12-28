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
            
        # 2. Build Context String for LLM
        citation_metadata = []
        
        if context_docs and len(context_docs) > 0:
            context_str = "CONTEXTO RECUPERADO:\n"
            for i, doc in enumerate(context_docs):
                meta = doc["metadata"]
                source_info = f"Fonte: {meta.get('filename')} ({meta.get('source')})"
                context_str += f"\n[Documento {i+1}] {source_info}\nConteúdo: {doc['content']}\n"
                
                # Prepara metadados para o frontend incluir o conteúdo no modal
                cite = meta.copy()
                cite["content"] = doc["content"]
                citation_metadata.append(cite)
        else:
            # Força o modelo a ver que não há nada, seguindo o novo protocolo bioético
            context_str = "CONTEXTO RECUPERADO:\n[SISTEMA: NENHUM DOCUMENTO ENCONTRADO NO BANCO DE DADOS LOCAL]\n"
        
        # 3. Load System Prompt from File
        from src.interfaces.api.routes.admin import PROMPT_FILE
        system_instructions = ""
        if PROMPT_FILE.exists():
            system_instructions = PROMPT_FILE.read_text(encoding="utf-8")
        
        # Merge system instructions with RAG context
        full_system_prompt = f"{system_instructions}\n\n{context_str}"
        
        # 4. Assemble Conversation for USUÁRIO vs ASSISTENTE
        conversation_history = ""
        if request.history:
            for msg in request.history:
                role = "USUÁRIO" if msg.role == "user" else "ASSISTENTE"
                conversation_history += f"{role}: {msg.content}\n"
        
        conversation_history += f"USUÁRIO: {request.message}\nASSISTENTE: "
        
        # 5. Generate Response
        response = await llm_client.generate(
            prompt=conversation_history, 
            system_prompt=full_system_prompt,
            images=request.images
        )
        
        # 5. Log Audit
        citation_names = ", ".join([m.get("filename", "unknown") for m in citation_metadata])
        prompt_version = "sentinela_prompt_v2" 
        
        # Calculate Confidence based on RAG retrieval scores
        rag_confidence = 0.0
        if context_docs:
            scores = [d.get("score", 0) for d in context_docs]
            if scores:
                rag_confidence = sum(scores) / len(scores)
        
        await db_manager.log_audit(
            action="chat_rag",
            details=f"Query: {request.message[:50]}... | Citations: {citation_names} | Prompt: {prompt_version}",
            user_hash=user_hash,
            confidence_score=rag_confidence
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
