import requests
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class LawScraper:
    """
    Ingestor especializado em "raspar" leis federais e estaduais diretamente do HTML.
    Garante integridade semântica para os chunks (Artigos).
    """

    def fetch_planalto_law(self, url: str, law_name: str) -> Dict:
        """
        Baixa uma lei do Planalto (ex: Código Florestal) e limpa para RAG.
        """
        headers = {
            'User-Agent': 'CivicSentinel/2.0 (Academic Research; Tinguá-RJ)'
        }
        
        try:
            logger.info(f"Baixando lei de {url}...")
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Decodificação correta (Planalto usa Latin-1 às vezes)
            response.encoding = response.apparent_encoding 
            
            raw_html = response.text
            clean_text, chunks = self.parse_html_content(raw_html, law_name)
            
            return {
                "source": url,
                "law_name": law_name,
                "full_text": clean_text,
                "chunks": chunks,  # Chunks já divididos por Artigo!
                "type": "legislation_html"
            }
            
        except Exception as e:
            logger.error(f"Erro ao baixar lei: {e}")
            return None

    def parse_html_content(self, html: str, law_name: str) -> Tuple[str, List[Dict]]:
        """
        Processa HTML bruto (seja local ou web) e retorna texto + chunks estruturados.
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # 1. Faxina: Remove menus, scripts, estilos, inputs e links de navegação
        # Também remove links (a) e textos riscados (strike, s, del) conforme pedido
        for tag in soup(["script", "style", "nav", "header", "footer", "form", "input", "button", "iframe", "a", "strike", "s", "del"]):
            tag.decompose()
            
        # Tenta focar no conteúdo principal se existir (comum no Planalto)
        body = soup.find('body') or soup
        
        # Preserva quebras de linha duplas para ajudar na separação semântica
        text_content = body.get_text(separator="\n\n")
        
        # 2. Chunking Semântico com Hierarquia
        # Regex para capturar Artigos E marcadores de estrutura (Título, Capítulo, Seção, etc.)
        pattern = re.compile(
            r'([ \t]*(?:TÍTULO|CAPÍTULO|SEÇÃO|SUBSEÇÃO|Art\.)\s+[IVXLCDM\dº]+.*?)(?=\n\n\s*(?:TÍTULO|CAPÍTULO|SEÇÃO|SUBSEÇÃO|Art\.)\s+[IVXLCDM\dº]+|$)', 
            re.DOTALL | re.IGNORECASE
        )
        
        raw_parts = pattern.findall(text_content)
        
        structured_chunks = []
        current_hierarchy = {
            "titulo": "",
            "capitulo": "",
            "secao": "",
            "subsecao": ""
        }
        
        # 3. Capturar Preâmbulo / Ementa (texto antes do primeiro marcador)
        first_match = pattern.search(text_content)
        if first_match:
            preamble_text = text_content[:first_match.start()].strip()
            if len(preamble_text) > 20:
                clean_preamble = re.sub(r'\(?Vide.*?\d{4}.*?\)?', '', preamble_text, flags=re.IGNORECASE)
                clean_preamble = " ".join(clean_preamble.split())
                structured_chunks.append({
                    "text": clean_preamble,
                    "metadata": {
                        "law_name": law_name,
                        "chunk_type": "preamble",
                        "article_index": 0
                    }
                })

        # 4. Processar Partes (Artigos e Hierarquia)
        article_count = 0
        if raw_parts:
            logger.info(f"⚖️ Detectadas {len(raw_parts)} partes (Artigos/Estrutura) via Regex.")
            for p in raw_parts:
                clean_part = re.sub(r'\(?Vide.*?\d{4}.*?\)?', '', p, flags=re.IGNORECASE)
                clean_part = " ".join(clean_part.split())
                
                if not clean_part: continue
                
                # Identifica se é um marcador de hierarquia
                is_header = False
                levels_map = {
                    "TÍTULO": "titulo",
                    "CAPÍTULO": "capitulo",
                    "SEÇÃO": "secao",
                    "SUBSEÇÃO": "subsecao"
                }
                
                for label, key in levels_map.items():
                    if clean_part.upper().startswith(label):
                        current_hierarchy[key] = clean_part
                        # Limpa níveis inferiores ao mudar um superior
                        levels_keys = ["titulo", "capitulo", "secao", "subsecao"]
                        idx = levels_keys.index(key)
                        for l in levels_keys[idx+1:]:
                            current_hierarchy[l] = ""
                        is_header = True
                        break
                
                # Se for Artigo, cria o chunk com o contexto atual
                if not is_header and clean_part.lower().startswith("art."):
                    article_count += 1
                    meta = {
                        "law_name": law_name,
                        "chunk_type": "article",
                        "article_index": article_count,
                        "is_article": True
                    }
                    # Adiciona hierarquia atual aos metadados
                    for k, v in current_hierarchy.items():
                        if v: meta[k] = v
                        
                    # Filter out artifacts (e.g. just "Art. 1" with no text)
                    if len(clean_part) < 15:
                        logger.warning(f"⚠️ Snippet muito curto ignorado: {clean_part}")
                        continue

                    # Always attempt to split by Incisos for better granularity
                    # But only if it actually creates more chunks.
                    from src.utils.text_processing import text_splitter
                    
                    # Extract header for context (e.g. "Art. 5º")
                    header_match = re.match(r"(Art\.\s*[\d\wº]+)", clean_part)
                    header = header_match.group(1) if header_match else "Art."
                    
                    # Remove header from body for processing? No, subsplit expects header separate.
                    # But clean_part has BOTH. 
                    # text_splitter.subsplit_law_chunk expects (header, body)
                    # We need to split them first.
                    
                    body_text = clean_part[len(header):].strip()
                    
                    # Try Granular Split (Incisos/Paragraphs)
                    # We force it if > 500 chars (approx 1 incision is usually < 200)
                    processed_chunks = []
                    
                    if len(body_text) > 400 or " I " in clean_part or "-\n" in clean_part or ";" in clean_part:
                         sub_parts = text_splitter.subsplit_law_chunk(header, body_text)
                         if len(sub_parts) > 1:
                              # Created multiple granular chunks
                              for i, part in enumerate(sub_parts):
                                  sub_meta = meta.copy()
                                  sub_meta["chunk_type"] = "article_part"
                                  sub_meta["part_index"] = i
                                  processed_chunks.append({
                                      "text": part,
                                      "metadata": sub_meta
                                  })
                         else:
                              # No split happened or just one chunk returned
                              processed_chunks.append({"text": clean_part, "metadata": meta})
                    else:
                         processed_chunks.append({"text": clean_part, "metadata": meta})
                         
                    structured_chunks.extend(processed_chunks)
        else:
            logger.warning("⚠️ Nenhum padrão detectado. Usando split simples.")
            structured_chunks = [{
                "text": " ".join(text_content.split())[:8000], 
                "metadata": {"source": law_name, "is_article": False}
            }]
                
        return text_content, structured_chunks
                
        return text_content, structured_chunks

# --- Exemplo de Uso (Pode rodar para testar) ---
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = LawScraper()
    
    # Ex: Código Florestal (Lei 12.651) - Fundamental para Tinguá
    url_florestal = "http://www.planalto.gov.br/ccivil_03/_ato2011-2014/2012/lei/l12651.htm"
    # Note: Requests might block if running from some clouds, works locally usually.
    
    print("Testando scraper...")
    # Mocking fetch for safety if internet blocked
    # dados = scraper.fetch_planalto_law(url_florestal, "Código Florestal")
    
    # if dados:
    #     print(f"Lei baixada: {dados['law_name']}")
    #     print(f"Total de Artigos extraídos: {len(dados['chunks'])}")
    #     print("Exemplo de Chunk (Artigo):")
    #     print(dados['chunks'][5]['text'][:200] + "...")
