# Infraestrutura e Segurança 🛡️

Este documento detalha a arquitetura de baixo nível, as medidas de proteção de dados e a stack tecnológica do Sentinela Cívico.

## 1. Stack Tecnológica Core

### Backend & AI
*   **Linguagem**: Python 3.10+ (Assíncrono com FastAPI).
*   **LLM Runner**: **Ollama** (Rodando localmente para suporte nativo a Metal/GPU em Mac M2).
*   **Modelo**: Gemma 3 (Open Weights).
*   **Vector Database**: ChromaDB (Persistência local).
*   **Relational Database**: SQLite 3 (Modo WAL habilitado para alta concorrência).

### Processamento de Documentos
*   **OCR Engine**: Tesseract OCR (via `pytesseract`).
*   **PDF Processing**: `pdf2image` + `poppler` para conversão de páginas de PDF em imagens de alta densidade antes do OCR.
*   **Visão Computacional**: Fallback automático para **Gemma Vision** (Gemma3 multimodal) quando a confiança do Tesseract é inferior ao limiar configurado.

---

## 2. Segurança e Privacidade (Privacy by Design)

O Sentinela foi projetado sob o princípio da **Soberania Digital**. Os dados nunca saem da infraestrutura controlada pelo usuário.

### Proteção de Identidade
*   **Hashing de Usuário (Argon2id)**: Implementamos o padrão ouro `Argon2id` para anonimização.
    *   **Determinismo**: Utilizamos um sistema de *Pepper* (Chave Estática) derivado do `ANONYMIZATION_SALT` no `.env`. Isso garante que a mesma identidade gere sempre o mesmo hash privativo, permitindo histórico sem rastreabilidade nominal.
    *   **Configuração**: `time_cost=2`, `memory_cost=65536`. Este equilíbrio oferece alta resistência a ataques de força bruta mantendo uma latência imperceptível (~20ms) para interações de chat.
*   **PII Scrubbing**: Um filtro baseado em Regex intercepta mensagens antes do envio ao LLM, removendo CPFs, E-mails e Telefones.

### Integridade de Dados
*   **Quarentena (Staging)**: Todos os documentos ingeridos entram em estado `pending`. Um administrador humano deve validar a qualidade da extração antes que os dados sejam injetados no índice vetorial (ChromaDB).
*   **Atomic Deletion**: Exclusão sincronizada entre SQLite e ChromaDB para garantir que nenhum rastro de um documento deletado permaneça no sistema.

---

## 3. Infraestrutura e Deploy

### Ambiente de Execução
*   **Conteinerização**: O sistema é projetado para rodar em Docker, isolando dependências e sistema de arquivos.
*   **Exceção de Hardware**: O **Ollama** deve rodar fora do contêiner em dispositivos Apple Silicon (Mac M1/M2/M3) para garantir acesso direto à aceleração Metal, otimizando a velocidade de inferência.

### Configurações Dinâmicas (Admin)
O sistema permite o ajuste fino de parâmetros críticos via interface administrativa:
*   **OCR Vision Threshold**: Limiar de confiança (0-100) que define quando o sistema desiste do Tesseract e aciona o modelo de Visão.
*   **Active Listening Threshold**: Sensibilidade para detecção de ambiguidade na pergunta do usuário.
*   **RAG Top-K**: Quantidade de fragmentos recuperados para compor a resposta.

---

*Última Atualização: Dezembro de 2025*
