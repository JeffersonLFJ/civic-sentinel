import logging
from typing import List, Dict, Any
from sentence_transformers import CrossEncoder
import torch

logger = logging.getLogger(__name__)

class Reranker:
    """
    Re-ranks search results using a Cross-Encoder model.
    A Cross-Encoder looks at (query, document) pairs simultaneously to output a relevance score,
    which is much more accurate than bi-encoder (vector) similarity but computationally expensive.
    Usage: Retrieve Top-K (high) -> Rerank -> Select Top-N (low) for LLM.
    """
    
    _model_name = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    _model = None

    @classmethod
    def get_model(cls):
        """
        Lazy loader for the model.
        """
        if cls._model is None:
            logger.info(f"⏳ Loading Reranker model: {cls._model_name}...")
            # Use CPU by default to avoid complexity, or detect CUDA/MPS
            device = "cpu"
            if torch.cuda.is_available():
                device = "cuda"
            elif torch.backends.mps.is_available():
                 device = "mps"
                 
            cls._model = CrossEncoder(cls._model_name, device=device)
            logger.info("✅ Reranker model loaded.")
        return cls._model

    @classmethod
    def rerank(cls, query: str, documents: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Reranks a list of document strings based on the query.
        Returns sorted indices and scores.
        """
        if not documents:
            return []
            
        model = cls.get_model()
        
        # Prepare pairs [ [query, doc1], [query, doc2], ... ]
        pairs = [[query, doc] for doc in documents]
        
        # Predict scores
        scores = model.predict(pairs)
        
        # Sort by score descending
        # Zip with original index to keep track
        scored_results = []
        for idx, score in enumerate(scores):
            scored_results.append({
                "index": idx,
                "score": float(score),
                "content": documents[idx] # Echo content for convenience
            })
            
        # Sort
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        
        return scored_results[:top_k]

reranker = Reranker()
