import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from src.core.llm_client import llm_client
from src.utils.security import anonymize_user
from src.utils.privacy import pii_scrubber

router = APIRouter()
logger = logging.getLogger(__name__)

class Message(BaseModel):
    role: str # 'user' or 'assistant'
    content: str

class ChatRequest(BaseModel):
    message: str
    user_id: str
    fingerprint: Optional[str] = None # Device fingerprint
    history: Optional[List[Message]] = None
    images: Optional[List[str]] = None
    # Active Listening Fields
    confirmation_mode: bool = False
    pending_intent: Optional[str] = None
    stream: bool = True # Default to Premium Streaming

async def interpret_intent(message: str) -> dict:
    """
    Motor Silencioso de Raciocínio (Backend).
    Função: Extrair termos de busca para o RAG e detectar se precisa de busca.
    NÃO gera texto de conversa.
    """
    
    # Prompt focado puramente em lógica e extração de dados
    from src.core.settings_manager import settings_manager
    system_prompt = settings_manager.intent_prompt
    
    prompt = f"Input usuário: '{message}'"
    
    try:
        # Force JSON mode
        response = await llm_client.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.1, # Temperatura baixa para precisão lógica
            json_mode=True
        )
        import json
        return json.loads(response["content"])
    except Exception as e:
        # Fallback safe
        return {
            "search_needed": True,
            "is_confirmation": False,
            "formal_query": message,
            "understood_intent": message,
            "ambiguity_score": 0.0
        }

@router.post("/")
async def chat_endpoint(request: ChatRequest):
    """
    Conversational endpoint with Active Listening, RAG and Memory.
    Supports SSE Streaming if requested (client should handle stream).
    For now, we default to streaming if client accepts text/event-stream, 
    but to keep it simple for this prototype, we'll return a StreamingResponse.
    """
    from fastapi.responses import StreamingResponse
    import json
    import asyncio
    from src.core.database import db_manager
    from src.core.settings_manager import settings_manager

    # 1. Identity Resolution (Fingerprint Priority)
    identity_source = request.fingerprint if request.fingerprint else request.user_id
    user_hash = anonymize_user(identity_source)
    
    # 2. PII Scrubbing (Privacy Layer)
    clean_message = pii_scrubber.scrub(request.message)
    request.message = clean_message
    
    try:
        # --- SILENT ENGINE ANALYTICS ---
        intent_data = await interpret_intent(request.message)
        
        # Decide Query Final e Esfera
        final_query = intent_data.get("formal_query", request.message)
        intent_sphere = intent_data.get("sphere", "unknown")
        search_needed = intent_data.get("search_needed", True)
        is_confirmation = intent_data.get("is_confirmation", False)
        ambiguity_score = intent_data.get("ambiguity_score", 0.0)
        
        # Check Configurable Threshold (ACTIVE LISTENING)
        listening_threshold = settings_manager.active_listening_threshold
        if ambiguity_score > listening_threshold and not is_confirmation:
             # Stop and Ask (Escuta Ativa)
             
             ambiguity_response_text = f"Desculpe, sua pergunta parece ter múltiplos sentidos. Você se refere a {intent_data.get('understood_intent', 'algo específico')} ou outro tópico? (Score de Ambiguidade: {ambiguity_score})"
             
             # Log Audit for Ambiguity Check
             await db_manager.log_audit(
                action="active_listening_check",
                user_hash=user_hash,
                query_text=request.message,
                response_text=ambiguity_response_text,
                sources_json="[]",
                confidence_score=ambiguity_score,
                details=json.dumps({
                    "intent": intent_data,
                    "trigger": "ambiguity_threshold_exceeded"
                })
             )

             # Return a structured JSON response immediately (no stream for this interruption)
             return {
                 "status": "ambiguity_detected",
                 "response": ambiguity_response_text,
                 "metadata": {
                     "ambiguity_score": ambiguity_score,
                     "intent_data": intent_data
                 }
             }
        
        # Override se o usuário explicitamente confirmou via UI
        if request.confirmation_mode and request.pending_intent:
             final_query = request.pending_intent
             search_needed = True 
             
        # 3. Retrieve Context (ONLY IF NEEDED)
        context_docs = []
        citation_metadata = []
        
        if search_needed and not is_confirmation:
            # 0. HyDE Strategy (DISABLED per User Request)
            # User opted for Keyword Extraction strategy instead of Hallucinated Vectors for now.
            hyde_vector_query = final_query
            
            # 1. Hybrid Retrieval Strategy
            vector_candidates = []
            keyword_candidates = []
            
            # Extract Keywords from Intent (created by Gemma)
            # If model failed to return list, fallback to splitting formal_query
            search_keywords = intent_data.get("keywords", [])
            if not search_keywords and final_query:
                # Fallback: simple split if no keywords returned
                search_keywords = final_query.split()
            
            # A. Vector Search
            keyword_candidates = []
            
            # A. Vector Search
            # A. Vector Search
            where_filter = None
            if intent_sphere != "unknown":
                where_filter = {"sphere": intent_sphere}
            
            vector_task = db_manager.search_documents(
                hyde_vector_query, 
                limit=settings_manager.rag_top_k,
                where=where_filter
            )
            # B. Keyword Search
            # B. Keyword Search
            # Ensure keywords is a string for FTS
            keyword_query_str = " ".join(search_keywords) if isinstance(search_keywords, list) else str(search_keywords)
            
            keyword_task = db_manager.search_documents_keyword(
                keyword_query_str, 
                limit=settings_manager.rag_top_k,
                sphere=intent_sphere if intent_sphere != "unknown" else None
            )
            
            vector_candidates, keyword_candidates = await asyncio.gather(vector_task, keyword_task)
            
            # Process Keyword Docs
            from src.utils.text_processing import text_splitter
            processed_keyword_candidates = []
            for kdoc in keyword_candidates:
                k_chunks = text_splitter.split(kdoc["content"], context_prefix=f"[{kdoc['metadata']['filename']}] ")
                for i, chunk_text in enumerate(k_chunks[:3]):
                   processed_keyword_candidates.append({
                        "content": chunk_text,
                        "metadata": kdoc["metadata"],
                        "score": 0.5 
                   })
            
            # C. Merge & Deduplicate
            all_candidates = vector_candidates + processed_keyword_candidates
            unique_candidates = {}
            import hashlib
            for cand in all_candidates:
                h = hashlib.md5(cand["content"].encode()).hexdigest()
                if h not in unique_candidates:
                    unique_candidates[h] = cand
            
            deduped_list = list(unique_candidates.values())
            
            # D. Re-ranking (Cross-Encoder)
            final_context_docs = []
            if deduped_list:
                 from src.core.reranker import reranker
                 candidate_texts = [d["content"] for d in deduped_list]
                 ranked_indices = reranker.rerank(final_query, candidate_texts, top_k=5)
                 
                 seen_primary_keys = set()
                 for item in ranked_indices:
                     chunk_doc = deduped_list[item["index"]]
                     original_doc_id = chunk_doc["metadata"].get("original_doc_id")
                     chunk_index = chunk_doc["metadata"].get("chunk_index")
                     parent_id = chunk_doc["metadata"].get("parent_id")
                     
                     dedupe_key = parent_id if parent_id else f"{original_doc_id}_{chunk_index}"
                     
                     if dedupe_key not in seen_primary_keys:
                         seen_primary_keys.add(dedupe_key)
                         retrieved_content = None
                         strategy_name = "raw_chunk"
                         
                         if parent_id:
                             retrieved_content = await db_manager.get_parent_content(parent_id)
                             strategy_name = "parent_retrieval"
                             
                         if not retrieved_content and original_doc_id and chunk_index is not None:
                             retrieved_content = await db_manager.get_context_window(original_doc_id, chunk_index, window_size=1)
                             strategy_name = "window_expansion"
                             
                         if retrieved_content:
                             full_doc = chunk_doc.copy()
                             full_doc["content"] = retrieved_content 
                             full_doc["score"] = item["score"]
                             full_doc["metadata"]["retrieval_strategy"] = strategy_name
                             final_context_docs.append(full_doc)
                         else:
                             chunk_doc["score"] = item["score"]
                             final_context_docs.append(chunk_doc)
            
            context_docs = final_context_docs

        # 2. Build Context String
        if context_docs and len(context_docs) > 0:
            context_str = "CONTEXTO RECUPERADO (Ordenado por Relevância):\n"
            for i, doc in enumerate(context_docs):
                meta = doc["metadata"]
                filename = meta.get('filename', 'Desconhecido')
                score_display = f"{doc['score']:.2f}"
                source = meta.get('source', 'Fonte Desconhecida').upper()
                date_pub = meta.get('publication_date', 'Data não informada')
                doc_type = meta.get('doc_type', 'documento_geral').lower()
                sphere_meta = meta.get('sphere', 'Não informada').upper()
                
                header = (
                    f"[DOCUMENTO {i+1}: {filename}]\n"
                    f"Autoridade: {source}\n"
                    f"Esfera: {sphere_meta}\n"
                    f"Publicado: {date_pub}\n"
                    f"Tipo: {doc_type}\n"
                    f"Score Relevância: {score_display}\n"
                    f"----------------"
                )
                context_str += f"\n{header}\n{doc['content']}\n"
                
                cite = meta.copy()
                cite["content"] = doc["content"]
                cite["relevance_score"] = doc["score"]
                citation_metadata.append(cite)
        else:
            context_str = "CONTEXTO RECUPERADO:\n[SISTEMA: NENHUM DOCUMENTO ENCONTRADO NO BANCO DE DADOS LOCAL]\n"
        
        # 3. Load System Prompt logic
        system_instructions = settings_manager.system_prompt
        if not system_instructions:
            from src.interfaces.api.routes.admin import PROMPT_FILE
            if PROMPT_FILE.exists():
                system_instructions = PROMPT_FILE.read_text(encoding="utf-8")
        
        full_system_prompt = f"{system_instructions}\n\n{context_str}"
        
        # 4. Assemble Conversation
        conversation_history = ""
        if request.history:
            for msg in request.history:
                role = "USUÁRIO" if msg.role == "user" else "ASSISTENTE"
                conversation_history += f"{role}: {msg.content}\n"
        
        conversation_history += f"USUÁRIO: {request.message}\n"
        if request.confirmation_mode and request.pending_intent:
             conversation_history = conversation_history.replace(f"USUÁRIO: {request.message}", f"USUÁRIO: {final_query}")

        conversation_history += "ASSISTENTE: "
        
        # --- STREAMING RESPONSE ---
        if request.stream:
            async def event_generator():
                full_response_text = ""
                
                # 1. Yield Citations First
                if citation_metadata:
                     yield json.dumps({"type": "citations", "data": citation_metadata}) + "\n"
                
                # 2. Yield Token Stream
                async for chunk in llm_client.generate_stream(
                    prompt=conversation_history,
                    system_prompt=full_system_prompt,
                    images=request.images,
                    temperature=settings_manager.temperature,
                    top_k=settings_manager.top_k,
                    num_ctx=settings_manager.num_ctx
                ):
                    content = chunk["content"]
                    full_response_text += content
                    yield json.dumps({"type": "token", "content": content}) + "\n"
                    
                # 3. Log Audit AFTER Stream
                citation_names = ", ".join([m.get("filename", "unknown") for m in citation_metadata])
                prompt_version = "sentinela_prompt_v2" 
                
                rag_confidence = 0.0
                if context_docs:
                    scores = [d.get("score", 0) for d in context_docs]
                    if scores:
                        avg_score = sum(scores) / len(scores)
                        rag_confidence = min(1.0, round(avg_score * 1.25, 2))
                
                sources_json_str = json.dumps(citation_metadata)
                clean_response_log = pii_scrubber.scrub(full_response_text)
                
                await db_manager.log_audit(
                    action="chat_rag_stream",
                    user_hash=user_hash,
                    query_text=request.message,
                    response_text=clean_response_log,
                    sources_json=sources_json_str,
                    confidence_score=rag_confidence,
                    details=json.dumps({
                        "intent": intent_data,
                        "prompt_version": prompt_version,
                        "model": settings_manager.llm_model,
                        "rag_count": len(citation_metadata)
                    })
                )
                
                yield json.dumps({"type": "done", "status": "complete"}) + "\n"

            return StreamingResponse(event_generator(), media_type="application/x-ndjson")

        # --- STANDARD JSON RESPONSE (Legacy/Test Compliance) ---
        else:
            response = await llm_client.generate(
                prompt=conversation_history, 
                system_prompt=full_system_prompt,
                images=request.images,
                temperature=settings_manager.temperature,
                top_k=settings_manager.top_k,
                num_ctx=settings_manager.num_ctx
            )
            
            # Log Audit
            citation_names = ", ".join([m.get("filename", "unknown") for m in citation_metadata])
            prompt_version = "sentinela_prompt_v2" 
            
            rag_confidence = 0.0
            if context_docs:
                scores = [d.get("score", 0) for d in context_docs]
                if scores:
                    avg_score = sum(scores) / len(scores)
                    rag_confidence = min(1.0, round(avg_score * 1.25, 2))
            
            sources_json_str = json.dumps(citation_metadata)
            clean_response_log = pii_scrubber.scrub(response["content"])
            
            logger.info("💾 Logging audit for standard chat...")
            await db_manager.log_audit(
                action="chat_rag_standard",
                user_hash=user_hash,
                query_text=request.message,
                response_text=clean_response_log,
                sources_json=sources_json_str,
                confidence_score=rag_confidence,
                details=json.dumps({
                    "intent": intent_data,
                    "prompt_version": prompt_version,
                    "model": response["model"],
                    "rag_count": len(citation_metadata)
                }, default=str)
            )
            logger.info("✅ Audit logged successfully.")
            
            return {
                "response": response["content"], 
                "metadata": {
                    "model": response["model"],
                    "timestamp": response["timestamp"],
                    "citations": citation_metadata
                }
            }

    except Exception as e:
        import traceback
        logger.error(f"Chat Endpoint Error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
