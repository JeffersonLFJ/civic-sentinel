import httpx
import asyncio
from datetime import date
from typing import List, Dict, Optional
import logging
import os
import tempfile
from src.core.ocr_engine import ocr_engine

logger = logging.getLogger(__name__)

class QueridoDiarioIngestor:
    """
    Ingestor otimizado para a API do Querido Diário com paginação e retry.
    """
    
    BASE_URL = "https://queridodiario.ok.org.br/api/"
    NOVA_IGUACU_ID = "3303500"  # Código IBGE fixo para a Tese
    
    def __init__(self):
        # CABEÇALHOS CRÍTICOS PARA EVITAR BLOQUEIO (Browser Masquerading)
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://queridodiario.ok.org.br/",
            "Origin": "https://queridodiario.ok.org.br",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin"
        }
        
        # Timeout aumentado para downloads maiores e follow_redirects habilitado
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL, 
            headers=headers, 
            timeout=120,
            follow_redirects=True
        )

    async def fetch_gazettes(
        self, 
        since: date, 
        until: Optional[date] = None,
        keywords: Optional[List[str]] = None,
        territory_id: str = NOVA_IGUACU_ID
    ) -> List[Dict]:
        """
        Busca diários com paginação automática (scroll) e filtro de servidor.
        """
        all_gazettes = []
        offset = 0
        page_size = 10  # Tamanho padrão da página da API
        
        # Constrói a query string para filtro no servidor (pré-filtro)
        query_string = " ".join(keywords) if keywords else None

        logger.info(f"A iniciar recolha para {territory_id} desde {since}")

        while True:
            params = {
                "territory_ids": territory_id,
                "published_since": since.isoformat(),
                "offset": offset,
                "size": page_size,
                "sort_by": "published_on",
                "sort_direction": "desc"
            }
            if until:
                params["published_until"] = until.isoformat()
            if query_string:
                params["querystring"] = query_string # Filtra na fonte

            try:
                response = await self.client.get("gazettes", params=params)
                response.raise_for_status()
                data = response.json()
                
                gazettes_page = data.get("gazettes", [])
                total_found = data.get("total_gazettes", 0)
                
                if not gazettes_page:
                    break
                
                all_gazettes.extend(gazettes_page)
                logger.info(f"Página processada: {len(gazettes_page)} itens. Total acumulado: {len(all_gazettes)}/{total_found}")
                
                # Verifica se acabou
                if len(all_gazettes) >= total_found or len(gazettes_page) < page_size:
                    break
                
                offset += page_size
                await asyncio.sleep(0.5) # Rate limit "ético"

            except httpx.HTTPStatusError as e:
                logger.error(f"Erro HTTP {e.response.status_code}: {e}")
                break
            except ValueError as e:
                logger.error(f"Erro ao decodificar JSON (possível bloqueio): {e}")
                logger.debug(f"Conteúdo da resposta: {response.text[:500]}")
                break
            except Exception as e:
                logger.error(f"Erro de conexão: {e}")
                break
            
        return all_gazettes

    async def process_and_store(self, gazettes: List[Dict], keywords: List[str] = None):
        """
        Processa, faz download do texto full e armazena.
        """
        from src.core.database import db_manager
        
        # 1. Deduplicação (Mantém o mais recente do dia)
        dedup_map = {}
        for g in gazettes:
            # Garante que temos uma data
            pub_date = g.get("date")
            if pub_date:
                dedup_map[pub_date] = g
                
        unique_gazettes = list(dedup_map.values())
        
        for g in unique_gazettes:
            # 2. Estratégia de Download de Conteúdo
            full_text = ""
            
            # Tenta pegar a URL do TXT (Processado pelo Querido Diário)
            text_url = g.get("txt_url")
            
            if text_url:
                try:
                    # Tenta baixar o txt
                    r = await self.client.get(text_url)
                    r.raise_for_status()
                    full_text = r.text
                except Exception as e:
                    logger.warning(f"Falha ao baixar TXT de {g['date']}: {e}. Tentando URL original...")
            
            if not full_text:
                # Tenta baixar o PDF original se não houver texto disponível
                pdf_url = g.get("url")
                if pdf_url:
                    logger.info(f"Tentando extrair texto via OCR para {g['date']}...")
                    try:
                        # Baixa o PDF para um arquivo temporário
                        r = await self.client.get(pdf_url)
                        r.raise_for_status()
                        
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                            tmp.write(r.content)
                            tmp_path = tmp.name
                            
                        try:
                            # Executa o motor de OCR (que já lida com cascata de PDF Direto -> Tesseract -> Fallback Vision)
                            ocr_results = await ocr_engine.process_document(tmp_path, doc_type="diario_oficial")
                            full_text = ocr_results.get("extracted_text", "")
                            ocr_method = ocr_results.get("ocr_method", "ocr_fallback")
                        finally:
                            if os.path.exists(tmp_path):
                                os.remove(tmp_path)
                    except Exception as e:
                        logger.error(f"Falha ao processar PDF/OCR de {g['date']}: {e}")
            
            if not full_text:
                logger.warning(f"Ignorando {g['date']} - Sem texto extraível disponível na API ou via OCR.")
                continue

            # 3. Armazenamento
            doc_data = {
                "filename": f"DO_{g['territory_name']}_{g['date']}.txt",
                "source": "official_gazette", # Alterado para manter consistência com metadados
                "text_content": full_text,
                "ocr_method": ocr_method if 'ocr_method' in locals() else "querido_diario_api", 
                "url": g.get("url"),
                "publication_date": g.get("date")
            }
            
            # Chama o seu DatabaseManager existente
            doc_id = await db_manager.save_document_record(doc_data)
            
            # 4. CRITICAL: Indexing for RAG
            # Metadata for context injection
            metadata = {
                "source": "official_gazette",
                "date": g.get("date"),
                "territory": g.get("territory_name"),
                "url": g.get("url"),
                "filename": doc_data["filename"],
                "publication_date": g.get("date")
            }
            
            # Check for extra keywords filter if passed (though server side filtered already)
            # Keeping strictly relevant text.
            
            await db_manager.index_document_text(
                doc_id=doc_id, 
                text=full_text,
                metadata=metadata
            )
            
            logger.info(f"Guardado e indexado: Diário de {g['date']}")

    async def close(self):
        await self.client.aclose()

diario_ingestor = QueridoDiarioIngestor()
