import re
import logging
from typing import List

logger = logging.getLogger(__name__)

class PIIScrubber:
    """
    Remove Personally Identifiable Information (PII) from text.
    Targeting: CPFs, Emails, Phones, and Social Media handles/URLs.
    """
    
    def __init__(self):
        # Regex Patterns
        self.patterns = {
            "DATA_CPF": r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b",
            "DATA_EMAIL": r"\b[\w\.-]+@[\w\.-]+\.\w+\b",
            "DATA_PHONE": r"\(?\d{2}\)?\s?\d{4,5}-?\d{4}",
            "DATA_SOCIAL_URL": r"(https?://)?(www\.)?(instagram\.com|facebook\.com|twitter\.com|x\.com|linkedin\.com|tiktok\.com)/[\w\.-]+",
            "DATA_SOCIAL_HANDLE": r"@[\w\._]+" # Be careful with this one, might catch emails if not ordered correctly
        }
        
    def scrub(self, text: str) -> str:
        """
        Redacts PII from the input text.
        """
        if not text:
            return ""
            
        scrubbed_text = text
        
        # Order matters! Handle specific URLs before generic handles
        
        # 1. Social URLs
        scrubbed_text = re.sub(self.patterns["DATA_SOCIAL_URL"], "[LINK_REDE_SOCIAL_REMOVIDO]", scrubbed_text, flags=re.IGNORECASE)
        
        # 2. Emails (Specific format)
        scrubbed_text = re.sub(self.patterns["DATA_EMAIL"], "[EMAIL_REMOVIDO]", scrubbed_text)
        
        # 3. CPFs
        scrubbed_text = re.sub(self.patterns["DATA_CPF"], "[CPF_REMOVIDO]", scrubbed_text)
        
        # 4. Phones
        scrubbed_text = re.sub(self.patterns["DATA_PHONE"], "[TELEFONE_REMOVIDO]", scrubbed_text)
        
        # 5. Social Handles (e.g. @jefferson)
        # Avoid matching emails that were already replaced or are malformed
        # Only match @word starting with space or start of line
        scrubbed_text = re.sub(r"(^|\s)@[\w\._]+", r"\1[REDESOCIAL_REMOVIDO]", scrubbed_text)
        
        if scrubbed_text != text:
            logger.info("🛡️ PII Scrubber: Dados sensíveis anonimizados na mensagem.")
            
        return scrubbed_text

pii_scrubber = PIIScrubber()
