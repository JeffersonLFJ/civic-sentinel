import os
from src.config import settings
from src.core.settings_manager import settings_manager

PROMPT_FILE = settings.BASE_DIR / "sentinela_prompt_v2.md"

class DynamicPromptManager:
    """
    Slices the monolithic markdown prompt into logical components and 
    reassembles them dynamically based on the current conversation intent.
    """
    
    def __init__(self):
        # We'll rely on the settings_manager to provide the raw text if available,
        # otherwise we read the file.
        pass

    def _get_raw_prompt(self):
        if settings_manager.system_prompt:
            return settings_manager.system_prompt
        
        if PROMPT_FILE.exists():
            return PROMPT_FILE.read_text(encoding="utf-8")
        
        return ""

    def build_prompt(self, intent_data: dict, context_docs: list) -> str:
        """
        Builds a lean system prompt based on conversational needs.
        """
        raw_text = self._get_raw_prompt()
        if not raw_text:
            return ""

        # Slicing logic based on markdown headers
        sections = {}
        current_section = "CORE"
        sections[current_section] = []

        # Split by ### headers
        lines = raw_text.split('\n')
        for line in lines:
            if line.startswith('### '):
                current_section = line[4:].strip()
                sections[current_section] = [line]
            else:
                if current_section not in sections:
                    sections[current_section] = []
                sections[current_section].append(line)

        # Reassemble based on logic
        final_prompt_parts = []
        
        # 1. Always include Core Identity and basic conversational rules if they exist
        identity_key = next((k for k in sections.keys() if "IDENTIDADE" in k.upper()), None)
        if identity_key:
            final_prompt_parts.extend(sections[identity_key])
            
        gestao_key = next((k for k in sections.keys() if "GESTÃO" in k.upper()), None)
        if gestao_key:
            final_prompt_parts.extend(sections[gestao_key])

        seguranca_key = next((k for k in sections.keys() if "SEGURANÇA" in k.upper()), None)
        if seguranca_key:
            final_prompt_parts.extend(sections[seguranca_key])

        # 2. Add RAG rules ONLY if search was needed
        search_needed = intent_data.get("search_needed", False)
        if search_needed or context_docs:
            rag_key = next((k for k in sections.keys() if "RAG" in k.upper()), None)
            if rag_key:
                final_prompt_parts.extend(sections[rag_key])

        # 3. Add Legal Framework (Kelsen) ONLY if it's a legal query or if docs were found
        kelsen_key = next((k for k in sections.keys() if "MATRIZ" in k.upper() or "KELSEN" in k.upper()), None)
        if kelsen_key:
            # We assume it's legal if it searched OR if the sphere was detected
            sphere = intent_data.get("sphere", "unknown")
            is_legal_intent = sphere != "unknown" or len(context_docs) > 0
            if is_legal_intent:
                final_prompt_parts.extend(sections[kelsen_key])

        # 4. Add Civic Imagination ONLY if requested
        imagination_key = next((k for k in sections.keys() if "IMAGINAÇÃO" in k.upper()), None)
        if imagination_key:
            # Check keywords for triggers
            keywords_str = " ".join(intent_data.get("keywords", [])).lower()
            if "imagina" in keywords_str or "simula" in keywords_str or "como seria" in keywords_str:
                final_prompt_parts.extend(sections[imagination_key])

        # 5. Always include Scratchpad for memory capability
        scratchpad_key = next((k for k in sections.keys() if "SCRATCHPAD" in k.upper()), None)
        if scratchpad_key:
            final_prompt_parts.extend(sections[scratchpad_key])

        # Fallback if somehow slicing failed (e.g., user removed all headers)
        if len(final_prompt_parts) == 0:
            return raw_text

        return "\n".join(final_prompt_parts)

dynamic_prompt_builder = DynamicPromptManager()
