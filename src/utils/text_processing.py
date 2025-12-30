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
            # Use Semantic Splitting for General Docs (with fallback inside)
            chunks = self.split_semantically(text)
            
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

    def split_pages(self, text: str) -> List[str]:
        """
        Splits text into pages using Form Feed (\f) marker.
        Used as 'Parent' chunk for General Documents (PDFs).
        """
        if "\f" not in text:
            # Fallback for texts without page markers (e.g. valid txt files)
            # Just treat as one page or split by length if huge?
            # Let's return as single 'Page' unless > 10k chars?
            if len(text) > 10000:
                return self.split_sliding_window(text, chunk_size=5000, overlap=100)
            return [text]
            
        return [page.strip() for page in text.split("\f") if page.strip()]

    def split_legal_acts(self, text: str) -> List[str]:
        """
        Splits Official Gazette into Administrative Acts (Decretos, Portarias).
        Used as 'Parent' chunk.
        """
        # Regex for common acts
        # We look for Start of Line + Keyword + Number
        # ex: "DECRETO Nº 1.234"
        pattern = r"((?:^|\n)\s*(?:DECRETO|PORTARIA|RESOLUÇÃO|LEI|ATA|EXTRATO|EDITAL)\s+(?:N[º°]?)?\s*[\d\./-]+.*?)(?=\n\s*(?:DECRETO|PORTARIA|RESOLUÇÃO|LEI|ATA|EXTRATO|EDITAL)\s+(?:N[º°]?)?\s*[\d\./-]+|$)"
        
        chunks = re.split(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        
        # Clean up
        final = []
        # Re-assemble captured groups (split returns [pre, delimiter, body, delimiter, body...])
        # Actually pattern above has capture group around the WHOLE block?
        # My pattern: (Start...Content)(?=Next)
        # re.split with capture group returns the group.
        # But this pattern captures the WHOLE act in group 1.
        # So split returning [empty, ACT1, empty, ACT2...]
        
        # Use findall is safer for this 'extract full blocks' pattern
        matches = re.findall(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        
        if not matches:
             # Fallback: Sliding Window if no structure found
             return self.split_sliding_window(text, chunk_size=4000, overlap=200)
             
        return [m.strip() for m in matches if m.strip()]



    def split_by_paragraphs(self, text: str, max_chars: int = 1500, overlap: int = 0) -> List[str]:
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
            current_chunk_parts = []
            current_len = 0
            
            for part in parts:
                part_len = len(part) + (len(separator) if separator else 0)
                
                if current_len + part_len > max_chars:
                    # Current chunk is full, verify integrity
                    if current_chunk_parts:
                        chunk_text = separator.join(current_chunk_parts)
                        final_chunks.append(chunk_text)
                        
                        # Handle overlap
                        if overlap > 0 and len(chunk_text) > overlap:
                             # Keep last parts that fit in overlap size
                             overlap_buffer = []
                             overlap_len = 0
                             for p in reversed(current_chunk_parts):
                                 p_len = len(p) + len(separator)
                                 if overlap_len + p_len < overlap:
                                     overlap_buffer.insert(0, p)
                                     overlap_len += p_len
                                 else:
                                     break
                             current_chunk_parts = overlap_buffer
                             current_len = overlap_len
                        else:
                             current_chunk_parts = []
                             current_len = 0
                    
                    # If single part is huge, recurse
                    if part_len > max_chars:
                         sub_chunks = recursive_split(part, current_separator_idx + 1)
                         final_chunks.extend(sub_chunks)
                    else:
                         current_chunk_parts.append(part)
                         current_len += part_len
                else:
                    current_chunk_parts.append(part)
                    current_len += part_len
            
            if current_chunk_parts:
                final_chunks.append(separator.join(current_chunk_parts))
                
            return final_chunks

        # Initial clean up
        text = re.sub(r'\n{3,}', '\n\n', text)
        return recursive_split(text, 0)

    def split_table(self, rows: List[List[str]], chunk_size: int = 50) -> List[str]:
        """
        Splits a large table (list of rows) into multiple Markup tables, 
        repeating the header for each chunk.
        """
        if not rows:
            return []
            
        header = rows[0]
        data_rows = rows[1:]
        
        if not data_rows:
            return []
            
        # Helper to format markdown
        def to_markdown(rh, rd):
            # Calculate column widths (simple version)
            # Actually we can just join with pipes
            # | Header | Header |
            # | --- | --- |
            # | Data | Data |
            
            md = "| " + " | ".join(str(x) for x in rh) + " |\n"
            md += "| " + " | ".join(["---"] * len(rh)) + " |\n"
            for row in rd:
                 md += "| " + " | ".join(str(x) for x in row) + " |\n"
            return md

        chunks = []
        for i in range(0, len(data_rows), chunk_size):
            chunk_rows = data_rows[i:i+chunk_size]
            table_chunk = to_markdown(header, chunk_rows)
            # Add context about paging
            page_info = f"\n*(Tabela: Linhas {i+1} a {i+len(chunk_rows)})*\n"
            chunks.append(table_chunk + page_info)
            
        return chunks

    def split_markdown_table(self, markdown_text: str, chunk_rows: int = 5) -> List[str]:
        """
        Splits a Markdown table string into smaller table chunks.
        Preserves header rows (| Header |... | --- |).
        """
        lines = markdown_text.strip().split('\n')
        # Need at least header (2 lines) and body
        if len(lines) < 3: 
            return [markdown_text]
            
        header_rows = []
        data_rows = []
        
        # Heuristic: First 2 lines are header if specific pattern
        if "|" in lines[0] and "-|-" in lines[1]:
             header_rows = lines[:2]
             data_rows = lines[2:]
        else:
             # Just split raw lines if not a standard table
             return self.split_by_paragraphs(markdown_text, max_chars=1000)
             
        chunks = []
        
        for i in range(0, len(data_rows), chunk_rows):
            chunk_data = data_rows[i:i+chunk_rows]
            # Reconstruct table
            mini_table = "\n".join(header_rows + chunk_data)
            chunks.append(mini_table)
            
        return chunks

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


    def split_semantically(self, text: str, window_size: int = 3, min_chunk_chars: int = 100) -> List[str]:
        """
        Splits text based on semantic similarity of sentence groups.
        Logic:
        1. Tokenize sentences.
        2. Create windows of size 'window_size' (e.g. 3 sentences).
        3. embed(Group i) vs embed(Group i+1) -> Similarity.
        4. Calculate dynamic threshold (Mean - StdDev).
        5. Split at valleys (local minima < threshold).
        6. Merge tiny chunks (< min_chunk_chars) with neighbors.
        """
        try:
            from sentence_transformers import SentenceTransformer, util
            import numpy as np
        except ImportError:
            # Fallback if dependencies missing
            return self.split_by_paragraphs(text)

        # 1. Cheap Sentence Tokenization (Regex is 99% good enough here)
        sentences = re.split(r'(?<=[.?!])\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) < window_size * 2:
             return [text]

        # Lazy load model (singleton pattern ideally, but local var for safety now)
        # Using all-MiniLM-L6-v2 (fast, ~80MB)
        model = SentenceTransformer('all-MiniLM-L6-v2') 
        
        # 2. Group Sentences (Sliding Window)
        # We compare Window A [0,1,2] vs Window B [1,2,3] is too close.
        # We want adjacent "Topics".
        # Let's try: Window A [0,1,2] vs Window B [3,4,5]? 
        # User said "Compare Grupo de 3 frases vs. PROXIMO Grupo".
        # Non-overlapping adjacent windows?
        # If we do sliding, we get smoother curve.
        # Let's do: Calculate embedding for EVERY sentence.
        # Then calculate similarity of Window(i-w:i) vs Window(i:i+w).
        
        embeddings = model.encode(sentences, convert_to_tensor=True)
        
        distances = []
        # Calculate cosine similarity between adjacent groups of 'window_size'
        # Point 'i' is the potential split point BETWEEN s[i-1] and s[i]
        # Left Context: s[i-window : i]
        # Right Context: s[i : i+window]
        
        valid_split_indices = []
        
        for i in range(window_size, len(sentences) - window_size):
            # Aggregate embeddings? Average them is a good proxy for "Topic Vector"
            left_emb = util.cos_sim(embeddings[i-window_size:i].mean(dim=0), embeddings[i:i+window_size].mean(dim=0))
            sim_score = left_emb.item()
            distances.append(sim_score)
            valid_split_indices.append(i)
            
        # 3. Dynamic Threshold
        if not distances:
            return [text]
            
        dist_np = np.array(distances)
        mean_sim = np.mean(dist_np)
        std_sim = np.std(dist_np)
        
        # We cut where similarity is LOW (Valley).
        # Threshold: statistically significant drop
        threshold = mean_sim - (0.5 * std_sim) # 0.5 sigma drop
        
        split_points = []
        for idx, score in zip(valid_split_indices, distances):
            if score < threshold:
                split_points.append(idx)
                
        # 4. Construct Chunks
        final_chunks = []
        current_start = 0
        
        # Add end of text
        split_points.append(len(sentences))
        
        for split_idx in split_points:
            # Check if this split is too close to previous? (Micro-chunk logic step 1)
            # Actually user asked for "Force Union" AFTER creation.
            
            chunk_sents = sentences[current_start:split_idx]
            chunk_text = " ".join(chunk_sents)
            final_chunks.append(chunk_text)
            current_start = split_idx
            
        # 5. Merge Micro-Chunks (The "Joiner")
        # Iterative pass: forward merge
        merged_chunks = []
        buffer_chunk = ""
        
        i = 0
        while i < len(final_chunks):
            current = final_chunks[i]
            
            # If buffer exists, prepend it
            if buffer_chunk:
                current = buffer_chunk + " " + current
                buffer_chunk = ""
                
            # Check size
            if len(current) < min_chunk_chars:
                # Merge with NEXT if possible
                if i + 1 < len(final_chunks):
                    buffer_chunk = current # Carry forward to next iteration
                else:
                    # Last chunk is tiny. Append to PREVIOUS if exists.
                    if merged_chunks:
                        merged_chunks[-1] += " " + current
                    else:
                         merged_chunks.append(current) # Only one tiny chunk
            else:
                merged_chunks.append(current)
            i += 1
            
        return merged_chunks

text_splitter = SmartTextSplitter()
