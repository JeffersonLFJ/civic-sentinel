import json
import logging
from pathlib import Path
from src.config import settings
from typing import Dict, Any

logger = logging.getLogger(__name__)

SETTINGS_FILE = settings.DATA_DIR / "runtime_settings.json"

DEFAULT_SETTINGS = {
    # Modelo / Cognição
    "llm_temperature": 0.1,
    "llm_top_k": 40, # Generation sampling
    "llm_num_ctx": 8192, # Context Window (Tokens)
    "system_prompt": "", # Empty means use default from file
    
    # Decisão / Escuta Ativa
    "active_listening_threshold": 0.8, # Ambiguity score to trigger confirmation
    "min_relevance_score": 0.4, # Minimum partial score to context inclusion
    "rag_top_k": 50, # Number of documents to retrieve
    
    # OCR
    "ocr_validation_threshold": 80.0, # Tesseract confidence to trigger Vision fallback
    
    # Sistema
    "context_window_size": 20, # Message History (Legacy/User View)
    
    # Prompts
    "intent_prompt": (
        "Você é um motor de NLP para um sistema cívico. Estruture dados para busca vetorial. "
        "Não seja educado, seja cirúrgico.\n\n"
        "REGRAS DE EXTRAÇÃO:\n"
        "1. Identifique a INTENÇÃO REAL (ex: 'posto fechado' -> 'denuncia_funcionamento_ubs').\n"
        "2. Se for conversa fiada ('oi', 'quem é você') ou perguntas sobre o sistema, marque search_needed = false.\n"
        "3. Se for confirmação ('sim', 'isso'), marque is_confirmation = true.\n"
        "4. Identifique a ESFERA (sphere): 'federal', 'estadual', 'municipal' ou 'unknown'.\n"
        "   - COMPETÊNCIA CONCORRENTE: Para temas amplos (Meio Ambiente, Saúde, Educação, Trânsito) ou perguntas teóricas ('O que é X?'), "
        "RETORNE 'unknown' para buscar em TODAS as esferas.\n"
        "   - Restrinja a 'municipal' APENAS se houver citação explícita de local/cidade ('em Nova Iguaçu', 'nesta cidade').\n"
        "5. Extraia PALAVRAS-CHAVE (keywords): Liste 3 a 5 termos essenciais para busca textual (OR logic). Ignore conectivos.\n"
        "\n"
        "Retorne APENAS JSON:\n"
        "{\n"
        '  "search_needed": <bool>,\n'
        '  "is_confirmation": <bool>,\n'
        '  "keywords": ["termo1", "termo2", "termo3"],\n'
        '  "formal_query": "<frase completa otimizada>",\n'
        '  "understood_intent": "<resumo curto>",\n'
        '  "sphere": "<federal|estadual|municipal|unknown>",\n'
        '  "ambiguity_score": <float 0.0-1.0>\n'
        "}"
    )
}

class SettingsManager:
    """
    Manages dynamic runtime settings for Sentinela.
    Persists data to JSON so it survives restarts.
    """
    
    def __init__(self):
        self._settings = DEFAULT_SETTINGS.copy()
        self.load()
        
    def load(self):
        """Loads settings from JSON file."""
        try:
            if SETTINGS_FILE.exists():
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                    self._settings.update(saved)
                    logger.info("⚙️ Configurações dinâmicas carregadas.")
            else:
                logger.info("⚙️ Usando configurações padrão (arquivo novo).")
                self.save()
        except Exception as e:
            logger.error(f"❌ Erro ao carregar settings: {e}")
            
    def save(self):
        """Persists current settings to JSON."""
        try:
            # Ensure dir
            SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"❌ Erro ao salvar settings: {e}")

    def get_all(self) -> Dict[str, Any]:
        return self._settings.copy()
        
    def update(self, updates: Dict[str, Any]):
        """Updates settings with validation."""
        # Simple validation could go here
        self._settings.update(updates)
        self.save()
        
    def get(self, key: str, default=None):
        return self._settings.get(key, default)

    # Specific Helpers
    
    @property
    def temperature(self) -> float:
        return float(self._settings.get("llm_temperature", 0.1))
        
    @property
    def top_k(self) -> int:
        return int(self._settings.get("llm_top_k", 40))
        
    @property
    def active_listening_threshold(self) -> float:
        return float(self._settings.get("active_listening_threshold", 0.8))
    
    @property
    def min_relevance_score(self) -> float:
        return float(self._settings.get("min_relevance_score", 0.4))

    @property
    def system_prompt(self) -> str:
        return self._settings.get("system_prompt", "")

    @property
    def num_ctx(self) -> int:
        return int(self._settings.get("llm_num_ctx", 8192))
        
    @property
    def rag_top_k(self) -> int:
        return int(self._settings.get("rag_top_k", 5))

    @property
    def ocr_validation_threshold(self) -> float:
        return float(self._settings.get("ocr_validation_threshold", 80.0))

    @property
    def intent_prompt(self) -> str:
        return self._settings.get("intent_prompt", "")


settings_manager = SettingsManager()
