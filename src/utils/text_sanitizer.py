"""
Post-processing sanitizer for text extracted by Docling or OCR engines.
Removes common artifacts that pollute the RAG index.
"""
import re
import logging

logger = logging.getLogger(__name__)


def sanitize_extracted_text(text: str) -> str:
    """
    Cleans extracted text before chunking and indexing.
    Removes:
    - Docling image placeholder tags (<!-- image -->)
    - Excessive dot sequences from table-of-contents (........)
    - Unicode garbled characters from bad OCR
    - Excessive whitespace and blank lines
    """
    if not text:
        return ""
    
    original_len = len(text)
    
    # 1. Remove Docling image placeholders
    text = re.sub(r'<!--\s*image\s*-->', '', text)
    
    # 2. Remove excessive dot/period sequences (table of contents lines)
    # Matches 5+ consecutive dots with optional spaces between them
    text = re.sub(r'[.\s]{5,}(?=\s*\||\s*\d|\s*$)', '... ', text, flags=re.MULTILINE)
    
    # 3. Remove garbled Unicode sequences (common OCR artifacts)
    # Matches sequences of 3+ non-latin characters in a row (Cyrillic, CJK mixed garbage)
    text = re.sub(r'[а-яА-ЯЁёảвМ]{3,}', '', text)
    
    # 4. Remove excessive blank lines (more than 2 consecutive)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # 5. Remove lines that are ONLY whitespace
    text = re.sub(r'^\s+$', '', text, flags=re.MULTILINE)
    
    # 6. Collapse multiple spaces into one
    text = re.sub(r'  +', ' ', text)
    
    # 7. Strip leading/trailing whitespace
    text = text.strip()
    
    cleaned_len = len(text)
    if original_len - cleaned_len > 100:
        logger.info(f"🧹 Sanitizer removed {original_len - cleaned_len} chars of noise ({((original_len - cleaned_len)/original_len)*100:.1f}% reduction)")
    
    return text
