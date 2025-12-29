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
        
        # Regex for hierarchy detection (lines starting with TITULO, CAPITULO, etc)
        # Matches: "CAPÍTULO I", "Seção II", "TÍTULO III" case insensitive
        hierarchy_pattern = re.compile(r"(?:^|\n)\s*(LIVRO|TÍTULO|CAPÍTULO|SEÇÃO|SUBSEÇÃO)\s+([IVXLCDM\d]+)(?:.{0,100})", re.IGNORECASE)
        
        
        # Better State Management
        hierarchy_state = {}
        hierarchy_levels = {"LIVRO": 1, "TÍTULO": 2, "CAPÍTULO": 3, "SEÇÃO": 4, "SUBSEÇÃO": 5}

        for i in range(0, len(chunks), 2):
            if i+1 < len(chunks):
                header = chunks[i].strip() # e.g., "Art. 1º"
                body = chunks[i+1]
                
                # 1. Build Context String from current state
                # Sort by level (1 to 5)
                active_context = [
                    hierarchy_state[k] for k in sorted(hierarchy_state.keys(), key=lambda x: hierarchy_levels.get(x, 99))
                ]
                context_str = " > ".join(active_context)
                
                combined = (header + " " + body).strip()
                
                # Prepend context!
                if context_str:
                    combined = f"[{context_str}] {combined}"
                
                # 2. Check for NEW hierarchy in this body to update state for NEXT chunks
                matches = list(hierarchy_pattern.finditer(body))
                for m in matches:
                    full_match = m.group(0).strip().replace("\n", " ") # Flatten
                    type_key = m.group(1).upper() # CAPÍTULO, TÍTULO...
                    
                    # Update State: set this type
                    hierarchy_state[type_key] = full_match
                    
                    # Clear any deeper levels (e.g. if Chapter found, clear Section)
                    current_lvl = hierarchy_levels.get(type_key, 99)
                    keys_to_remove = [k for k, v in hierarchy_levels.items() if v > current_lvl and k in hierarchy_state]
                    for k in keys_to_remove:
                        del hierarchy_state[k]

                # Check size. If huge, sub-split by Paragraphs/Items
                if len(combined) > 2500:
                    # Sub-split logic
                    sub_chunks = self._subsplit_law_chunk(header, body, context_prefix=f"[{context_str}] " if context_str else "")
                    final_chunks.extend(sub_chunks)
                else:
                    final_chunks.append(combined)
            else:
                 if chunks[i].strip():
                     final_chunks.append(chunks[i].strip())
                     
        return [c for c in final_chunks if c]


    def _subsplit_law_chunk(self, header: str, body: str, context_prefix: str = "") -> List[str]:
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
                sub_chunks.append(f"{context_prefix}{header} {parts[0].strip()}")
            
            for k in range(1, len(parts), 2):
                if k+1 < len(parts):
                    para_header = parts[k].strip()
                    para_body = parts[k+1]
                    # Inject Parent Header
                    sub_chunks.append(f"{context_prefix}{header} > {para_header} {para_body}".strip())
            return sub_chunks
            
        # Fallback: simple paragraph split if no § but huge
        paragraphs = self.split_by_paragraphs(body, max_chars=2000)
        return [f"{context_prefix}{header} (Cont.) {p}" for p in paragraphs]


    def split_by_paragraphs(self, text: str, max_chars: int = 1500) -> List[str]:
        """
        Smart recursive splitting trying to respect semantic boundaries.
        Priority: Double Newline > Single Newline > Sentence End > Space.
        """
        separators = ["\n\n", "\n", ". ", " ", ""]
        
        def recursive_split(text: str, current_separator_idx: int) -> List[str]:
            if len(text) <= max_chars:
                return [text]
            
            if current_separator_idx >= len(separators):
                # Fallback: Hard slice
                return [text[i:i+max_chars] for i in range(0, len(text), max_chars)]
            
            separator = separators[current_separator_idx]
            parts = text.split(separator) if separator else list(text)
            
            final_chunks = []
            current_buffer = ""
            
            for part in parts:
                # Re-add separator (except for last logic usually, simplified here)
                part_with_sep = part + separator if separator and separator != "\n\n" else part
                
                if len(current_buffer) + len(part_with_sep) <= max_chars:
                    current_buffer += part_with_sep
                else:
                    if current_buffer:
                        final_chunks.append(current_buffer)
                    
                    if len(part_with_sep) > max_chars:
                        # Recursion on the part that is too big
                        sub_chunks = recursive_split(part_with_sep, current_separator_idx + 1)
                        final_chunks.extend(sub_chunks)
                        current_buffer = ""
                    else:
                        current_buffer = part_with_sep
            
            if current_buffer:
                final_chunks.append(current_buffer)
                
            return final_chunks

        # Initial clean up of repeated newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        return recursive_split(text, 0)

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
