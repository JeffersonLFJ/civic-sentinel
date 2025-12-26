import re
from typing import List, Literal

class SmartTextSplitter:
    """
    Intelligent text splitter with specific strategies for different document types.
    """

    def split(self, text: str, doc_type: str = "general", context_prefix: str = "") -> List[str]:
        """
        Routes the splitting logic based on document type.
        Args:
            text: Content to split
            doc_type: 'legislation', 'diario_oficial', 'general'
            context_prefix: String to prepend to EVERY chunk (e.g. "[LEI 1234] ")
        """
        if not text:
            return []

        chunks = []
        if doc_type == "legislation" or "lei" in doc_type.lower():
            chunks = self.split_by_law_articles(text)
        elif doc_type == "diario_oficial" or "gazette" in doc_type.lower():
            chunks = self.split_sliding_window(text, chunk_size=3000, overlap=500)
        else:
            chunks = self.split_by_paragraphs(text)
            
        # Inject context (Source/Title) into every chunk if provided
        if context_prefix:
            chunks = [f"{context_prefix}{c}" for c in chunks]

        # Safety: Ensure no chunk is huge (fallback for failed regex splits)
        final_valid_chunks = []
        for c in chunks:
            if len(c) > 4000:
                # Force split huge chunks
                final_valid_chunks.extend(self.split_sliding_window(c, chunk_size=3000, overlap=500))
            else:
                final_valid_chunks.append(c)
            
        return final_valid_chunks

    def split_by_law_articles(self, text: str) -> List[str]:
        """
        Splits text by Legislation Articles (e.g., 'Art. 1º', 'Art. 10').
        Keeps the article header with the content.
        If a chunk is too large (>2000 chars), it further splits by paragraphs 
        but keeps the Article Header context.
        """
        # Regex to find "Art. <number>"
        # Matches: Art. 1, Art. 1º, Art. 10
        pattern = r"((?:^|\n)\s*Art\.?\s*\d+(?:[º°\.]?))"
        
        # Split but keep delimiters
        chunks = re.split(pattern, text, flags=re.IGNORECASE)
        
        final_chunks = []
        
        # Handle preamble
        if chunks and not re.match(r"\s*Art", chunks[0], re.IGNORECASE):
             if chunks[0].strip():
                 final_chunks.append(chunks[0].strip())
             chunks = chunks[1:]
        
        for i in range(0, len(chunks), 2):
            if i+1 < len(chunks):
                header = chunks[i].strip() # e.g., "Art. 1º"
                body = chunks[i+1]
                combined = (header + " " + body).strip()
                
                # Check size. If huge, sub-split by Paragraphs/Items
                if len(combined) > 2500:
                    # Sub-split logic
                    sub_chunks = self._subsplit_law_chunk(header, body)
                    final_chunks.extend(sub_chunks)
                else:
                    final_chunks.append(combined)
            else:
                 if chunks[i].strip():
                     final_chunks.append(chunks[i].strip())
                     
        return [c for c in final_chunks if c]

    def _subsplit_law_chunk(self, header: str, body: str) -> List[str]:
        """
        Splits a large Article body by Paragraphs (§) or Items (I, II, III).
        Prepends the 'header' to each child.
        """
        # Try splitting by Paragraph symbol '§'
        if "§" in body:
            parts = re.split(r"(§\s*\d+.*?)", body)
            sub_chunks = []
            # First part (caput)
            if parts[0].strip():
                sub_chunks.append(f"{header} {parts[0].strip()}")
            
            for k in range(1, len(parts), 2):
                if k+1 < len(parts):
                    para_header = parts[k].strip()
                    para_body = parts[k+1]
                    # Inject Parent Header
                    sub_chunks.append(f"{header} > {para_header} {para_body}".strip())
            return sub_chunks
            
        # Fallback: simple paragraph split if no § but huge
        paragraphs = self.split_by_paragraphs(body, max_chars=2000)
        return [f"{header} (Cont.) {p}" for p in paragraphs]


    def split_by_paragraphs(self, text: str, max_chars: int = 1500) -> List[str]:
        """
        Splits by double newlines, then aggregates up to max_chars.
        Good for Reports, Plans, Minutes.
        """
        raw_paragraphs = re.split(r"\n\s*\n", text)
        final_chunks = []
        current_chunk = ""
        
        for para in raw_paragraphs:
            para = para.strip()
            if not para:
                continue
                
            if len(current_chunk) + len(para) + 2 <= max_chars:
                current_chunk += "\n\n" + para if current_chunk else para
            else:
                if current_chunk:
                    final_chunks.append(current_chunk)
                current_chunk = para
                
        if current_chunk:
            final_chunks.append(current_chunk)
            
        return final_chunks

    def split_sliding_window(self, text: str, chunk_size: int = 3000, overlap: int = 500) -> List[str]:
        """
        Sliding window for continuous texts like Gazettes where context is key.
        """
        if len(text) <= chunk_size:
            return [text]
            
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            
            if end >= len(text):
                break
                
            start += (chunk_size - overlap)
            
        return chunks

text_splitter = SmartTextSplitter()
