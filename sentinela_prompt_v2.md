# INSTRUÇÃO DE GERAÇÃO DE CÓDIGO - PROJETO SENTINELA CÍVICO v2.0

## CONTEXTO ACADÊMICO
Este sistema é a implementação técnica de uma tese de doutorado em Bioética sobre **Justiça Epistêmica Algorítmica**. O código gerado deve servir como prova de conceito replicável para outros territórios vulneráveis no Brasil.

**Território-alvo:** Tinguá (Nova Iguaçu/RJ)  
**Hipótese central:** A burocracia estatal cria barreiras epistêmicas. IA local e open source pode atuar como equalizadora, promovendo acesso a direitos fundamentais.

---

## ROLE E RESTRIÇÕES BIOÉTICAS

**Atue como:** Arquiteto de Sistemas Críticos com especialização em Civic Tech e Ética em IA.

### Restrições Invioláveis (Princípios Bioéticos)

**1. Privacy by Design (Anonimato Total)**
- ZERO dados pessoais crus no sistema
- Hashing SHA256 com salt antes de qualquer I/O
- Logs anônimos vinculados por tokens de auditoria

**2. Auditabilidade Completa**
- Todo output da IA inclui metadados: timestamp, versão do prompt, nível de confiança
- Decisões automatizadas devem ser rastreáveis e explicáveis
- Sistema de versionamento de prompts obrigatório

**3. Fail-Safe (Segurança em Caso de Falha)**
- Em caso de incerteza (confiança < 70%), escalar para moderadores humanos
- Alertas de alta urgência exigem dupla validação (IA + humano)
- Fallbacks para todas as operações críticas

**4. Soberania Tecnológica**
- Nenhuma dependência de APIs proprietárias ou serviços em nuvem
- Processamento 100% on-premise
- Dados nunca saem do servidor local

---

## STACK TECNOLÓGICA COMPLETA

### Backend Core
```yaml
Linguagem: Python 3.11+
API Framework: FastAPI 0.104+
Type System: Pydantic 2.5+ (validação estrita)
Async Runtime: asyncio + uvloop
```

### Camada de Dados
```yaml
Vector Database: ChromaDB 0.4.18 (embeddings e busca semântica)
Relational Database: SQLite 3.40+ (metadados estruturados)
Cache: Redis 7.2 (opcional, para rate limiting)
```

### Inteligência Artificial

**LLM Principal:**
```yaml
Modelo: gemma3:27b-instruct
Servidor: Ollama 0.1.17
Capacidades: Texto + Visão (multimodal nativo)
Uso: Chat conversacional, análise semântica, validação de contexto
```

**Pipeline OCR Híbrido (3 Camadas):**

```yaml
Camada 1 - Tesseract 5.3+:
  Uso: Documentos limpos, texto impresso de qualidade
  Velocidade: Alta (CPU-only)
  Idioma: Português brasileiro (tesseract-ocr-por)
  
Camada 2 - PaddleOCR 2.7+:
  Uso: Tabelas complexas, orçamentos, planilhas
  Velocidade: Média (GPU recomendado)
  Diferencial: Preserva estrutura tabular
  
Camada 3 - DocTR 0.7+ (Hugging Face):
  Uso: PDFs nativos e escaneados
  Velocidade: Média (GPU recomendado)
  Diferencial: Detecta hierarquia (títulos, parágrafos, blocos)

Fallback - Gemma3 Vision:
  Uso: Validação de OCR, casos ambíguos, imagens sem texto
  Velocidade: Baixa (GPU obrigatório)
  Diferencial: Análise contextual e qualitativa
```

### Orquestração e Integração
```yaml
Containerização: Docker Compose 2.20+
Workflow Automation: n8n 1.16+
Gateway WhatsApp: Evolution API v2.0
Agendamento: APScheduler 3.10+ (dentro do Python)
```

### Interfaces de Usuário
```yaml
Admin Dashboard: Streamlit 1.29
Public Demo: Gradio 4.8
API Documentation: Swagger/ReDoc (auto-gerado pelo FastAPI)
```

---

## ARQUITETURA DE DIRETÓRIOS

```
sentinela_civico/
├── .env.example                 # Template de variáveis (NUNCA commitar .env real)
├── .gitignore                   # data/, logs/, .env, __pycache__
├── docker-compose.yml           # 6 serviços (ver seção Docker)
├── requirements.txt             # Dependências com versões pinadas
├── pyproject.toml               # Build config (Poetry ou Rye)
├── README.md                    # Documentação principal
├── LICENSE                      # GPL-3.0 ou AGPL-3.0 (copyleft forte)
│
├── data/                        # ⚠️ NÃO VERSIONADO (em .gitignore)
│   ├── chromadb/                # Persistência de vetores
│   ├── sqlite/                  # sentinela.db (metadados)
│   ├── uploads_temp/            # Uploads temporários (auto-delete 24h)
│   ├── processed/               # Documentos após OCR
│   └── models/                  # Cache de modelos Ollama (opcional)
│
├── prompts/                     # Sistema de versionamento de prompts
│   ├── CHANGELOG.md             # Log de mudanças nos prompts
│   ├── system_base_v1.md        # Prompt raiz do Sentinela
│   ├── bioethics_validator_v1.md # Validador de outputs
│   ├── ocr_contextualizer_v1.md # Prompt para análise pós-OCR
│   └── alert_templates/         # Templates de notificações
│       ├── patrimonio.md
│       ├── saude.md
│       └── legislacao.md
│
├── docs/                        # Documentação técnica
│   ├── ARCHITECTURE.md          # Visão geral do sistema
│   ├── DEPLOYMENT.md            # Guia de instalação
│   ├── REPLICATION_GUIDE.md     # Como adaptar para outro território
│   └── BIOETHICS_FRAMEWORK.md   # Fundamentação teórica
│
├── tests/                       # Suite de testes
│   ├── conftest.py              # Fixtures pytest
│   ├── test_security.py         # Validação de anonimização
│   ├── test_ocr_pipeline.py     # Qualidade de extração
│   ├── test_rag.py              # Relevância de busca vetorial
│   ├── test_bioethics.py        # Casos de viés conhecidos
│   └── test_integration.py      # Testes end-to-end
│
├── scripts/                     # Utilitários de manutenção
│   ├── setup_models.sh          # Download dos modelos Ollama
│   ├── ingest_diarios.py        # Script de ingestão inicial
│   └── backup_db.sh             # Backup automatizado
│
└── src/
    ├── __init__.py
    ├── config.py                # Settings (Pydantic BaseSettings)
    │
    ├── utils/
    │   ├── __init__.py
    │   ├── security.py          # Anonymization, RBAC, audit tokens
    │   ├── validators.py        # Schemas Pydantic (request/response)
    │   ├── text_processing.py   # Chunking, limpeza, normalização
    │   └── logging.py           # Logger estruturado (JSON format)
    │
    ├── core/
    │   ├── __init__.py
    │   ├── database.py          # Gerenciadores ChromaDB + SQLite
    │   ├── llm_client.py        # Cliente Ollama (texto + visão)
    │   ├── ocr_engine.py        # ⭐ Pipeline OCR híbrido (novo)
    │   └── prompt_manager.py    # Carrega/versiona prompts do /prompts
    │
    ├── ocr/                     # ⭐ Módulo OCR especializado (novo)
    │   ├── __init__.py
    │   ├── tesseract_processor.py   # Implementação Tesseract
    │   ├── paddle_processor.py      # Implementação PaddleOCR
    │   ├── doctr_processor.py       # Implementação DocTR
    │   ├── preprocessing.py         # Filtros de imagem (deskew, denoise)
    │   └── quality_validator.py     # Valida qualidade do OCR
    │
    ├── ingestors/
    │   ├── __init__.py
    │   ├── diario_oficial.py    # API Querido Diário
    │   ├── pdf_processor.py     # PyMuPDF + fallback para OCR
    │   ├── image_processor.py   # Pipeline: Imagem → OCR → Texto → Vetores
    │   └── base_ingestor.py     # Interface abstrata (ABC)
    │
    ├── reasoning/
    │   ├── __init__.py
    │   ├── rag_engine.py        # Busca vetorial + reranking
    │   ├── bioethics_filter.py  # Valida outputs (viés, toxicidade)
    │   ├── alert_classifier.py  # Categoriza urgência (baixa/média/alta)
    │   └── context_builder.py   # Monta contexto para o LLM
    │
    ├── interfaces/
    │   ├── __init__.py
    │   ├── api/
    │   │   ├── main.py          # FastAPI app principal
    │   │   ├── dependencies.py  # Injeção de dependências
    │   │   ├── routes/
    │   │   │   ├── __init__.py
    │   │   │   ├── chat.py      # Endpoint conversacional
    │   │   │   ├── upload.py    # Recebe denúncias/documentos
    │   │   │   ├── webhooks.py  # Callbacks do n8n
    │   │   │   ├── admin.py     # Endpoints administrativos
    │   │   │   └── health.py    # Monitoramento de saúde
    │   │   └── middleware.py    # Rate limit, CORS, logging, auth
    │   │
    │   └── admin/
    │       ├── app.py           # Streamlit dashboard principal
    │       ├── pages/           # Páginas do admin
    │       │   ├── documents.py      # Gestão de documentos
    │       │   ├── prompts.py        # Editor de prompts
    │       │   ├── analytics.py      # Métricas de uso
    │       │   └── moderation.py     # Fila de revisão humana
    │       └── components/      # Widgets reutilizáveis
    │
    └── workflows/               # Lógica de monitoramento autônomo
        ├── __init__.py
        ├── daily_scraper.py     # Monitora Diários Oficiais (agendado)
        ├── alert_dispatcher.py  # Envia notificações filtradas
        └── quality_monitor.py   # Monitora qualidade dos outputs da IA
```

---

## ESPECIFICAÇÕES DETALHADAS POR MÓDULO

### 1. `src/utils/security.py` - Camada de Segurança

```python
"""
Módulo crítico de segurança e privacidade.
Toda interação com dados pessoais passa por aqui.
"""

from hashlib import sha256
from typing import Literal
import secrets
import os

def anonymize_user(raw_id: str, salt: str = None) -> str:
    """
    CRITICAL: Esta função é a primeira linha de defesa.
    raw_id NUNCA deve ser persistido em logs, DB ou transmitido.
    
    Args:
        raw_id: Identificador original (ex: número de telefone)
        salt: Salt para hashing (deve vir do .env: ANONYMIZATION_SALT)
    
    Returns:
        Hash determinístico SHA256 (mesmo user = mesmo hash sempre)
    
    Exemplo:
        >>> anonymize_user("5521987654321", salt="my_secret_salt")
        'a3f5e8c9d1b2...'  # Hash de 64 caracteres
    """
    if not salt:
        salt = os.getenv("ANONYMIZATION_SALT")
        if not salt:
            raise ValueError("ANONYMIZATION_SALT não configurado no .env")
    
    # Concatena salt + raw_id e gera hash
    salted = f"{salt}{raw_id}".encode('utf-8')
    return sha256(salted).hexdigest()


def generate_audit_token() -> str:
    """
    Gera ID único para rastrear uma interação específica.
    Usado para vincular logs sem expor identidade do usuário.
    
    Returns:
        Token aleatório de 32 caracteres hexadecimais
    
    Exemplo:
        >>> generate_audit_token()
        '7f3a9e2c1d8b5f4a6e9c0d1b2a3f4e5c'
    """
    return secrets.token_hex(16)


RoleType = Literal["cidadao", "moderador", "admin"]

# Matriz de permissões (RBAC simplificado)
PERMISSIONS = {
    "cidadao": {
        "chat": True,
        "upload": True,
        "view_own_data": True,
        "delete_own_data": True,
        "moderate_alerts": False,
        "edit_prompts": False,
        "view_analytics": False
    },
    "moderador": {
        "chat": True,
        "upload": True,
        "view_own_data": True,
        "delete_own_data": True,
        "moderate_alerts": True,  # Pode revisar alertas
        "edit_prompts": False,
        "view_analytics": True
    },
    "admin": {
        # Acesso total
        "chat": True,
        "upload": True,
        "view_own_data": True,
        "delete_own_data": True,
        "moderate_alerts": True,
        "edit_prompts": True,
        "view_analytics": True,
        "manage_users": True
    }
}

def check_permission(role: RoleType, action: str) -> bool:
    """
    Verifica se uma role tem permissão para executar uma ação.
    
    Args:
        role: Tipo de usuário
        action: Ação a ser verificada (ex: "edit_prompts")
    
    Returns:
        True se permitido, False caso contrário
    
    Exemplo:
        >>> check_permission("cidadao", "edit_prompts")
        False
        >>> check_permission("admin", "edit_prompts")
        True
    """
    return PERMISSIONS.get(role, {}).get(action, False)


def sanitize_filename(filename: str) -> str:
    """
    Remove caracteres perigosos de nomes de arquivo.
    Previne path traversal attacks.
    
    Args:
        filename: Nome do arquivo original
    
    Returns:
        Nome sanitizado
    """
    import re
    # Remove path separators e caracteres especiais
    safe_name = re.sub(r'[^\w\s\-\.]', '', filename)
    # Remove .. (path traversal)
    safe_name = safe_name.replace('..', '')
    return safe_name
```

---

### 2. `src/core/ocr_engine.py` - Pipeline OCR Híbrido ⭐

```python
"""
Sistema de OCR adaptativo que escolhe a melhor ferramenta por contexto.
Prioriza velocidade e precisão, com fallback para LLM Vision quando necessário.
"""

from typing import Dict, Literal, Optional
from pathlib import Path
import asyncio
from datetime import datetime

# Importa os processadores específicos
from src.ocr.tesseract_processor import TesseractOCR
from src.ocr.paddle_processor import PaddleOCR
from src.ocr.doctr_processor import DocTROCR
from src.core.llm_client import GemmaVision

OCRMethod = Literal["tesseract", "paddle", "doctr", "gemma_vision", "auto", "hybrid"]
DocumentType = Literal["diario_oficial", "orcamento", "foto_denuncia", "auto"]


class OCREngine:
    """
    Gerenciador centralizado de OCR com fallbacks inteligentes.
    
    Pipeline de decisão:
    1. Detecta tipo de documento (PDF nativo, PDF escaneado, imagem)
    2. Escolhe melhor método OCR
    3. Executa extração
    4. Valida qualidade com Gemma Vision (se confiança < 80%)
    5. Enriquece com análise semântica
    """
    
    def __init__(self, config: Dict):
        """
        Args:
            config: Configurações do sistema (vem de src/config.py)
        """
        self.config = config
        
        # Inicializa todos os processadores
        self.tesseract = TesseractOCR(config)
        self.paddle = PaddleOCR(config)
        self.doctr = DocTROCR(config)
        self.gemma = GemmaVision(config)
        
        # Thresholds de qualidade
        self.MIN_CONFIDENCE = config.get("ocr_min_confidence", 70)
        self.VALIDATION_THRESHOLD = config.get("ocr_validation_threshold", 80)
    
    
    async def process_document(
        self, 
        file_path: str,
        doc_type: DocumentType = "auto",
        enable_validation: bool = True,
        enable_semantic_analysis: bool = True
    ) -> Dict:
        """
        Processa um documento com OCR adaptativo.
        
        Args:
            file_path: Caminho para o arquivo
            doc_type: Tipo do documento (auto-detecta se "auto")
            enable_validation: Se True, valida OCR com Gemma Vision
            enable_semantic_analysis: Se True, faz análise contextual
        
        Returns:
            {
                "extracted_text": str,
                "ocr_method": str,
                "confidence": float,
                "document_type": str,
                "semantic_analysis": dict (se habilitado),
                "validation": dict (se executado),
                "requires_human_review": bool,
                "processing_time_ms": float,
                "timestamp": str
            }
        """
        start_time = datetime.now()
        
        # Fase 1: Detecção de tipo
        if doc_type == "auto":
            doc_type = self._detect_document_type(file_path)
        
        # Fase 2: Extração com método apropriado
        ocr_result = await self._execute_ocr(file_path, doc_type)
        
        # Fase 3: Validação (se confiança baixa ou habilitado)
        validation_result = None
        if enable_validation and ocr_result["confidence"] < self.VALIDATION_THRESHOLD:
            validation_result = await self._validate_with_vision(
                text=ocr_result["text"],
                image_path=file_path,
                ocr_method=ocr_result["method"]
            )
            
            # Se validação falhou, tenta método alternativo
            if validation_result["recommended_action"] == "refazer_ocr":
                ocr_result = await self._execute_ocr(file_path, doc_type, force_method="hybrid")
        
        # Fase 4: Análise semântica
        semantic_analysis = None
        if enable_semantic_analysis:
            semantic_analysis = await self.gemma.contextualize(
                ocr_text=ocr_result["text"],
                document_type=doc_type,
                image_path=file_path if ocr_result["confidence"] < 90 else None
            )
        
        # Calcula tempo de processamento
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return {
            "extracted_text": ocr_result["text"],
            "ocr_method": ocr_result["method"],
            "confidence": ocr_result["confidence"],
            "document_type": doc_type,
            "semantic_analysis": semantic_analysis,
            "validation": validation_result,
            "requires_human_review": self._should_review(ocr_result, validation_result),
            "processing_time_ms": processing_time,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {
                "file_size_bytes": Path(file_path).stat().st_size,
                "file_extension": Path(file_path).suffix
            }
        }
    
    
    def _detect_document_type(self, file_path: str) -> DocumentType:
        """
        Detecta tipo do documento por extensão e conteúdo.
        
        Lógica:
        - .pdf com texto extraível → diario_oficial (padrão) ou orcamento
        - .pdf sem texto → foto_denuncia (PDF escaneado)
        - .jpg/.png → foto_denuncia
        """
        ext = Path(file_path).suffix.lower()
        
        if ext == '.pdf':
            try:
                import PyPDF2
                with open(file_path, 'rb') as f:
                    pdf = PyPDF2.PdfReader(f)
                    first_page = pdf.pages[0].extract_text()
                    
                    if len(first_page) > 100:  # PDF com texto
                        # Detecta por palavras-chave
                        text_lower = first_page.lower()
                        
                        if "diário oficial" in text_lower or "publicado" in text_lower:
                            return "diario_oficial"
                        elif any(kw in text_lower for kw in ["orçamento", "despesa", "receita", "loa", "ldo"]):
                            return "orcamento"
                        else:
                            return "diario_oficial"  # Default para PDFs
                    else:
                        # PDF escaneado (sem texto extraível)
                        return "foto_denuncia"
            except Exception as e:
                # Se falhar, trata como foto
                return "foto_denuncia"
        
        elif ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
            return "foto_denuncia"
        
        else:
            # Tipo desconhecido
            return "foto_denuncia"
    
    
    async def _execute_ocr(
        self, 
        file_path: str, 
        doc_type: DocumentType,
        force_method: Optional[OCRMethod] = None
    ) -> Dict:
        """
        Executa OCR com o método mais apropriado.
        
        Roteamento por tipo de documento:
        - diario_oficial → DocTR (PDFs nativos)
        - orcamento → PaddleOCR (preserva tabelas)
        - foto_denuncia → Tesseract (robusto para baixa qualidade)
        - hybrid → Tenta todos e pega melhor resultado
        """
        if force_method == "hybrid":
            return await self._hybrid_ocr(file_path)
        
        if force_method:
            method = force_method
        else:
            # Mapeamento automático
            method_map = {
                "diario_oficial": "doctr",
                "orcamento": "paddle",
                "foto_denuncia": "tesseract"
            }
            method = method_map.get(doc_type, "tesseract")
        
        # Executa o método escolhido
        if method == "tesseract":
            result = await self.tesseract.extract(file_path)
        elif method == "paddle":
            result = await self.paddle.extract(file_path)
        elif method == "doctr":
            result = await self.doctr.extract(file_path)
        elif method == "gemma_vision":
            result = await self.gemma.extract_text_from_image(file_path)
        else:
            raise ValueError(f"Método OCR desconhecido: {method}")
        
        return {
            "text": result["text"],
            "confidence": result["confidence"],
            "method": method
        }
    
    
    async def _hybrid_ocr(self, file_path: str) -> Dict:
        """
        Executa múltiplos métodos OCR e retorna o melhor resultado.
        Usado como fallback quando métodos individuais falham.
        """
        results = await asyncio.gather(
            self.tesseract.extract(file_path),
            self.paddle.extract(file_path),
            self.doctr.extract(file_path),
            return_exceptions=True  # Não falha se um método der erro
        )
        
        # Filtra erros e pega resultado com maior confiança
        valid_results = [r for r in results if isinstance(r, dict)]
        
        if not valid_results:
            # Todos falharam, usa Gemma Vision como último recurso
            gemma_result = await self.gemma.extract_text_from_image(file_path)
            return {
                "text": gemma_result["description"],
                "confidence": 0,  # Marca como não-numérico
                "method": "gemma_vision_fallback"
            }
        
        best_result = max(valid_results, key=lambda x: x.get("confidence", 0))
        
        return {
            "text": best_result["text"],
            "confidence": best_result["confidence"],
            "method": f"hybrid_{len(valid_results)}_methods"
        }
    
    
    async def _validate_with_vision(
        self, 
        text: str, 
        image_path: str,
        ocr_method: str
    ) -> Dict:
        """
        Usa Gemma Vision para validar se o OCR foi bem-sucedido.
        Compara texto extraído com análise visual da imagem.
        """
        return await self.gemma.validate_ocr_quality(
            ocr_text=text,
            image_path=image_path,
            ocr_method=ocr_method
        )
    
    
    def _should_review(
        self, 
        ocr_result: Dict, 
        validation_result: Optional[Dict]
    ) -> bool:
        """
        Decide se o resultado precisa revisão humana.
        
        Critérios:
        - Confiança < MIN_CONFIDENCE
        - Validação recomendou revisão
        - Texto muito curto (< 50 caracteres) quando esperado mais
        """
        # Confiança baixa
        if ocr_result["confidence"] < self.MIN_CONFIDENCE:
            return True
        
        # Validação explícita
        if validation_result and validation_result.get("recommended_action") == "revisar_humano":
            return True
        
        # Texto suspeito
        if len(ocr_result["text"]) < 50 and ocr_result["method"] != "gemma_vision":
            return True
        
        return False
```

---

### 3. `src/core/llm_client.py` - Cliente Gemma Unificado

```python
"""
Cliente unificado para Gemma3:27B (texto + visão).
Centraliza toda interação com o modelo LLM.
"""

import httpx
import json
import base64
from typing import Dict, List, Optional, Any
from pathlib import Path


class GemmaVision:
    """
    Cliente para Gemma3:27B rodando no Ollama.
    Suporta texto puro e análise de imagens (multimodal).
    """
    
    def __init__(self, config: Dict):
        """
        Args:
            config: Configurações do sistema (URL do Ollama, modelo, etc)
        """
        self.base_url = config.get("ollama_url", "http://ollama:11434")
        self.model = config.get("llm_model", "gemma3:27b")
        self.timeout = config.get("llm_timeout", 120)
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout
        )
    
    
    async def generate_response(
        self,
        prompt: str,
        context_docs: List[str] = None,
        system_prompt: str = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
        format: Optional[str] = None  # "json" para outputs estruturados
    ) -> Dict:
        """
        Gera resposta textual (sem imagens).
        
        Args:
            prompt: Pergunta/instrução do usuário
            context_docs: Documentos relevantes do RAG
            system_prompt: Prompt de sistema (identidade do Sentinela)
            temperature: 0-1 (0=determinístico, 1=criativo)
            max_tokens: Limite de tokens na resposta
            format: "json" se espera JSON estruturado
        
        Returns:
            {
                "text": str,
                "confidence": float (estimativa),
                "model_version": str,
                "timestamp": str
            }
        """
        # Monta contexto completo
        full_prompt = self._build_prompt(prompt, context_docs, system_prompt)
        
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "temperature": temperature,
            "num_predict": max_tokens,
            "stream": False
        }
        
        if format:
            payload["format"] = format
        
        response = await self.client.post("/api/generate", json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        return {
            "text": data["response"],
            "confidence": self._estimate_confidence(data),
            "model_version": self.model,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    
    async def contextualize(
        self,
        ocr_text: str,
        document_type: str,
        image_path: Optional[str] = None
    ) -> Dict:
        """
        Analisa semanticamente texto extraído por OCR.
        Usa visão se confiança do OCR for baixa.
        """
        # Se imagem estiver disponível, usa multimodalidade para enriquecer
        if image_path:
            # Converte imagem para base64
            with open(image_path, "rb") as img_file:
                image_b64 = base64.b64encode(img_file.read()).decode('utf-8')
                
            prompt = f"""
            Analise este documento e seu texto OCR.
            
            TEXTO OCR:
            {ocr_text[:2000]}... (truncado)
            
            Tarefa:
            1. Corrija erros óbvios de OCR no texto.
            2. Extraia entidades-chave (datas, valores, nomes).
            3. Resuma o propósito do documento.
            
            Retorne JSON estrito:
            {{
                "summary": "...",
                "entities": {{...}},
                "corrected_text_snippet": "..."
            }}
            """
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "images": [image_b64],
                "format": "json",
                "stream": False
            }
        else:
            # Apenas texto
            prompt = f"""
            Analise o seguinte texto extraído de um documento ({document_type}):
            
            {ocr_text[:3000]}
            
            Tarefa:
            1. Extraia metadados principais.
            2. Identifique urgência (Baixa/Média/Alta).
            
            Retorne JSON estrito.
            """
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "format": "json",
                "stream": False
            }
            
        response = await self.client.post("/api/generate", json=payload)
        response.raise_for_status()
        
        return json.loads(response.json()["response"])


    async def validate_ocr_quality(
        self,
        ocr_text: str,
        image_path: str,
        ocr_method: str
    ) -> Dict:
        """
        Usa visão para julgar se o OCR foi bem sucedido.
        """
        with open(image_path, "rb") as img_file:
            image_b64 = base64.b64encode(img_file.read()).decode('utf-8')
            
        prompt = f"""
        Atue como auditor de qualidade de OCR.
        
        Compare a imagem fornecida com este texto extraído pelo método '{ocr_method}':
        
        --- INÍCIO TEXTO OCR ---
        {ocr_text[:1000]}
        --- FIM TEXTO OCR ---
        
        Avalie de 0 a 100 a fidelidade do texto em relação à imagem.
        Se a nota for menor que 80, explique o motivo (ex: "tabela desformatada", "ruído", "texto ilegível").
        
        Retorne JSON:
        {{
            "quality_score": int,
            "issues": ["..."],
            "recommended_action": "aprovar" | "refazer_ocr" | "revisar_humano"
        }}
        """
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "images": [image_b64],
            "format": "json",
            "stream": False
        }
        
        response = await self.client.post("/api/generate", json=payload)
        return json.loads(response.json()["response"])


    def _build_prompt(self, prompt, context_docs, system_prompt):
        """Monta o prompt final com template estruturado."""
        # Lógica de template string...
        full_prompt = ""
        if system_prompt:
            full_prompt += f"SYSTEM: {system_prompt}\n\n"
            
        if context_docs:
            context_str = "\n---\n".join(context_docs)
            full_prompt += f"CONTEXTO RECUPERADO:\n{context_str}\n\n"
            
        full_prompt += f"USUÁRIO: {prompt}\nASSISTENTE:"
        return full_prompt

    def _estimate_confidence(self, response_data):
        """
        Tenta extrair confiança (se o modelo suportar logprobs) ou
        usa heurísticas baseadas na resposta.
        """
        # Placeholder para implementação futura com logprobs
        return 0.95

        GUIA DE DEPLOYMENT (DOCKER)
docker-compose.yml final

YAML
version: '3.8'

services:
  # 1. ORQUESTRADOR DE INTEGRAÇÕES
  n8n:
    image: n8nio/n8n:latest
    ports:
      - "5678:5678"
    volumes:
      - n8n_data:/home/node/.n8n
      - ./data:/data_shared
    environment:
      - N8N_SECURE_COOKIE=false
    networks:
      - sentinela-net

  # 2. BANCO VETORIAL
  chromadb:
    image: chromadb/chroma:latest
    volumes:
      - ./data/chromadb:/chroma/chroma
    ports:
      - "8000:8000"
    networks:
      - sentinela-net

  # 3. INTERFACE WHATSAPP
  evolution-api:
    image: atila/evolution-api:v1.8.2
    ports:
      - "8081:8080"
    environment:
      - AUTHENTICATION_API_KEY=${EVOLUTION_API_KEY}
    volumes:
      - evolution_instances:/evolution/instances
    networks:
      - sentinela-net

  # 4. LLM SERVER (OLLAMA)
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_models:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    networks:
      - sentinela-net

  # 5. CORE BACKEND (FASTAPI)
  api:
    build: 
      context: .
      dockerfile: Dockerfile
    command: uvicorn src.interfaces.api.main:app --host 0.0.0.0 --port 8080
    volumes:
      - ./data:/app/data
      - ./prompts:/app/prompts
    environment:
      - OLLAMA_URL=http://ollama:11434
      - CHROMA_URL=http://chromadb:8000
    depends_on:
      - ollama
      - chromadb
    networks:
      - sentinela-net

  # 6. ADMIN DASHBOARD (STREAMLIT)
  admin:
    build: 
      context: .
      dockerfile: Dockerfile
    command: streamlit run src/interfaces/admin/app.py
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data
      - ./prompts:/app/prompts
    networks:
      - sentinela-net

volumes:
  n8n_data:
  ollama_models:
  evolution_instances:

networks:
  sentinela-net:
    driver: bridge
CHECKLIST DE VALIDAÇÃO (ANTES DE RODAR)
Segurança: O salt de hash está configurado no .env?

Modelos: O modelo gemma3:27b foi baixado no Ollama (ollama pull gemma3:27b)?

Hardware: A máquina host tem VRAM suficiente (24GB+) para rodar o modelo quantizado? Caso contrário, configure fallback para gemma:7b no .env.

Dependências OCR: As bibliotecas de sistema (tesseract-ocr, libgl1) estão no Dockerfile?

FIM DA INSTRUÇÃO.