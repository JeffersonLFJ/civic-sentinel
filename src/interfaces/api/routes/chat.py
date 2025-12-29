from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from src.core.llm_client import llm_client
from src.utils.security import anonymize_user
from src.utils.privacy import pii_scrubber

router = APIRouter()

class Message(BaseModel):
    role: str # 'user' or 'assistant'
    content: str

class ChatRequest(BaseModel):
    message: str
    user_id: str
    fingerprint: Optional[str] = None # Device fingerprint
    history: Optional[List[Message]] = None
    images: Optional[List[str]] = None

@router.post("/")
async def chat_endpoint(request: ChatRequest):
    """
    Conversational endpoint with RAG and Memory.
    """
    # 1. Identity Resolution (Fingerprint Priority)
    identity_source = request.fingerprint if request.fingerprint else request.user_id
    user_hash = anonymize_user(identity_source)
    
    # 2. PII Scrubbing (Privacy Layer)
    clean_message = pii_scrubber.scrub(request.message)
    
    # Update request message effectively
    request.message = clean_message
    
    try:
        from src.core.database import db_manager
        
        # 1. Retrieve Context
        # 0. HyDE (Hypothetical Document Embeddings)
        # Generate a hypothetical answer to improve vector search recall
        hyde_vector_query = request.message
        
        # Only use HyDE for questions, not simple greetings (heuristic)
        if len(request.message) > 10 and "?" in request.message:
            hyde_prompt = (
                f"Escreva um parágrafo hipotético curto (3-4 frases) que responda à pergunta abaixo "
                f"com base em leis municipais ou documentos oficiais. "
                f"Use termos técnicos e linguagem formal. Não diga 'eu não sei'. "
                f"Apenas alucine uma resposta plausível para fins de busca vetorial.\n\n"
                f"Pergunta: {request.message}\n\n"
                f"Resposta Hipotética:"
            )
            try:
                # Fast generation for query expansion
                hyde_gen = await llm_client.generate(
                    prompt=hyde_prompt,
                    system_prompt="Você é um gerador de documentos simulados para busca vetorial.",
                    images=None
                )
                hyde_vector_query = hyde_gen["content"]
                # print(f"DEBUG HyDE: {hyde_vector_query}") # Uncomment for debug
            except Exception as e:
                # Fallback to original query if generation fails
                pass

        # 1. Hybrid Retrieval Strategy
        # Fetch candidates from Vector Store (Semantic using HyDE) and SQLite FTS (Keyword using Original)
        
        vector_candidates = []
        keyword_candidates = []
        
        if len(request.message) > 3:
            # Parallel execution? For simplicity in v1, sequential.
            # A. Vector Search (High recall, exploring meaning) -> Get 15
            # Uses HyDE text for better semantic matching
            vector_candidates = await db_manager.search_documents(hyde_vector_query, limit=15)
            
            # B. Keyword Search (Precision, specific terms like "Art. 5") -> Get 5 docs
            # Uses ORIGINAL query for precision
            keyword_docs = await db_manager.search_documents_keyword(request.message, limit=5)
            
            # Process Keyword Docs: they are full text, we need to chunk them to be comparable
            from src.utils.text_processing import text_splitter
            
            for kdoc in keyword_docs:
                # Split large keyword matches into chunks so Reranker can handle them
                # We limit to first 3 chunks to avoid flooding if doc is huge
                k_chunks = text_splitter.split(kdoc["content"], context_prefix=f"[{kdoc['metadata']['filename']}] ")
                for i, chunk_text in enumerate(k_chunks[:3]):
                    keyword_candidates.append({
                         "content": chunk_text,
                         "metadata": kdoc["metadata"],
                         "score": 0.5 # Dummy score
                    })

        # C. Merge & Deduplicate
        # Simple dedupe by content hash to avoid exact duplicates
        all_candidates = vector_candidates + keyword_candidates
        unique_candidates = {}
        
        import hashlib
        for cand in all_candidates:
            # Hash content for uniqueness check
            h = hashlib.md5(cand["content"].encode()).hexdigest()
            if h not in unique_candidates:
                unique_candidates[h] = cand
        
        deduped_list = list(unique_candidates.values())
        
        # D. Re-ranking (Cross-Encoder)
        # Select Top-5 most relevant from the mixed pool
        final_context_docs = []
        
        if deduped_list:
             from src.core.reranker import reranker
             # Extract texts
             candidate_texts = [d["content"] for d in deduped_list]
             
             # Rerank
             ranked_indices = reranker.rerank(request.message, candidate_texts, top_k=5)
             
             # Reconstruct sorted list
             for item in ranked_indices:
                 original_doc = deduped_list[item["index"]]
                 # Update score with the high-precision re-ranker score
                 original_doc["score"] = item["score"] 
                 final_context_docs.append(original_doc)
        
        context_docs = final_context_docs
        
        # 2. Build Context String for LLM
        citation_metadata = []
        
        if context_docs and len(context_docs) > 0:
            context_str = "CONTEXTO RECUPERADO (Ordenado por Relevância):\n"
            for i, doc in enumerate(context_docs):
                meta = doc["metadata"]
                # Add re-rank score to display
                score_display = f"{doc['score']:.2f}"
                source_info = f"Fonte: {meta.get('filename')} (Score: {score_display})"
                context_str += f"\n[Documento {i+1}] {source_info}\nConteúdo: {doc['content']}\n"
                
                # Prepara metadados para o frontend incluir o conteúdo no modal
                cite = meta.copy()
                cite["content"] = doc["content"]
                cite["relevance_score"] = doc["score"]
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
        
        # 5. Log Audit (Structured for Raio-X)
        citation_names = ", ".join([m.get("filename", "unknown") for m in citation_metadata])
        prompt_version = "sentinela_prompt_v2" 
        
        # Calculate Calibrated Confidence
        # Using a more balanced linear curve: min(1.0, avg_score * 1.25)
        # This prevents low confidence reports for decent retrieval (e.g. 0.6 -> 75%)
        rag_confidence = 0.0
        if context_docs:
            scores = [d.get("score", 0) for d in context_docs]
            if scores:
                avg_score = sum(scores) / len(scores)
                rag_confidence = min(1.0, round(avg_score * 1.25, 2))
        
        # Structure sources for JSON storage
        import json
        sources_json = json.dumps(citation_metadata)
        
        # SECURITY: Scrub response before logging (prevent LLM PII leaks)
        # Even if input was scrubbed, LLM might hallucinate or echo PII from context
        clean_response_log = pii_scrubber.scrub(response["content"])
        
        await db_manager.log_audit(
            action="chat_rag",
            user_hash=user_hash,
            query_text=request.message, # This was already scrubbed at entry
            response_text=clean_response_log,
            sources_json=sources_json,
            confidence_score=rag_confidence,
            details=f"Citations: {citation_names} | Prompt: {prompt_version}"
        )
        
        return {
            "response": response["content"], # Return raw to user (they are themselves), or scrubbed? 
            # Ideally user sees raw (mirroring), but LOG sees scrubbed.
            "metadata": {
                "model": response["model"],
                "timestamp": response["timestamp"],
                "citations": citation_metadata
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
