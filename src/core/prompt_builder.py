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

        # Slicing logic based on markdown headers and HTML triggers
        sections = {}
        section_triggers = {}
        current_section = "CORE"
        sections[current_section] = []
        section_triggers[current_section] = "always"

        # Split by ### headers
        lines = raw_text.split('\n')
        for line in lines:
            if line.startswith('### '):
                current_section = line[4:].strip()
                sections[current_section] = [line]
                section_triggers[current_section] = "always" # default
            elif line.startswith('<!-- trigger:'):
                trigger_rule = line.replace('<!-- trigger:', '').replace('-->', '').strip()
                section_triggers[current_section] = trigger_rule
            else:
                if current_section not in sections:
                    sections[current_section] = []
                sections[current_section].append(line)

        # Reassemble based on logic
        final_prompt_parts = []
        
        search_needed = intent_data.get("search_needed", False)
        sphere = intent_data.get("sphere", "unknown")
        keywords_str = " ".join(intent_data.get("keywords", [])).lower()
        has_docs = len(context_docs) > 0
        
        # Regex fallback for legal
        import re
        legal_pattern = r"\b(lei|decreto|artigo|inciso|constituição|portaria|stf|jurisprudência)\b"
        user_msg = intent_data.get("user_message", "").lower()
        has_legal_regex = bool(re.search(legal_pattern, user_msg))

        for sec_name, sec_lines in sections.items():
            rule = section_triggers.get(sec_name, "always")
            
            should_include = False
            if rule == "always":
                should_include = True
            elif rule == "search=true":
                if search_needed or has_docs:
                    should_include = True
            elif rule == "intent=legal":
                if sphere != "unknown" or has_docs or has_legal_regex:
                    should_include = True
            elif rule == "intent=imagination":
                if "imagina" in keywords_str or "simula" in keywords_str or "como seria" in keywords_str:
                    should_include = True
            else:
                should_include = True # fallback
                
            if should_include:
                final_prompt_parts.extend(sec_lines)

        # Fallback if somehow slicing failed (e.g., user removed all headers)
        if len(final_prompt_parts) == 0:
            return raw_text

        return "\n".join(final_prompt_parts)

dynamic_prompt_builder = DynamicPromptManager()
