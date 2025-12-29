# 🦅 Relatório Técnico: Sentinela Cívico

**Versão**: 1.0  
**Data**: 28 de Dezembro de 2024  
**Desenvolvedor Principal**: Jefferson Lopes (Direção Criativa/Vibe)  
**Co-Piloto AI**: Google Gemini 3 (High & Flash) via AntiGravity CLI

---

## 1. Visão Geral do Projeto/Produto
O **Sentinela Cívico** é uma plataforma de monitoramento, auditoria e simplificação de documentos públicos (Diários Oficiais, Leis e Contratos). Diferente de soluções tradicionais de busca por palavra-chave, o Sentinela utiliza **Inteligência Artificial Generativa Local (Local LLM)** e **RAG (Retrieval-Augmented Generation)** para "ler", entender o contexto e responder perguntas complexas sobre a administração pública, garantindo **soberania de dados** e **privacidade total**.

## 2. Metodologia de Desenvolvimento: "Vibe Coding"
A construção do Sentinela seguiu o paradigma emergente de **"Vibe Coding"**, onde o desenvolvedor humano atua menos como um digitador de sintaxe e mais como um **Diretor de Orquestra** ou **Arquiteto de Intenção**.

### O Papel dos Agentes (Google AntiGravity)
Utilizando a CLI **Google AntiGravity**, o projeto foi desenvolvido em parcerias de "pair programming" de alta frequência com agentes de IA (Gemini 3 High e Flash).
- **O Humano (Jefferson)**: Definiu o *vibe* (a intenção, a regra de negócio, a ética, o design visual e a aprovação final).
- **A IA (Gemini)**: Executou a implementação, refatoração, correção de bugs, criação de testes e sugestões arquiteturais em tempo real.
- **Resultado**: Um ciclo de desenvolvimento acelerado (horas ao invés de semanas) com código robusto e documentado.

---

## 3. Arquitetura Técnica

O sistema opera em uma arquitetura modular focada em independência e processamento local.

### 🛠 Stack Tecnológica
*   **Backend**: Python 3.10+ com **FastAPI** (Assíncrono, rápido e padronizado).
*   **Frontend**: HTML5/JS Vanilla + CSS Moderno (Glassmorphism, Responsivo).
*   **Banco de Dados**:
    *   **SQLite**: Metadados, Logs de Auditoria e Usuários.
    *   **ChromaDB**: Banco vetorial para armazenamento de *embeddings* (memória semântica).
*   **Inteligência Artificial (O Cérebro)**:
    *   **Ollama**: Runtime local para inferência de LLMs.
    *   **Modelo Principal**: `gemma3:27b`.

### 🧩 Módulos Principais

#### A. Ingestão Híbrida Inteligente
O sistema utiliza uma abordagem multi-modal para lidar com a "sujeira" e variedade dos dados públicos:

1.  **Monitoramento Automático (API Querido Diário)**: Integração via API com o projeto 'Querido Diário' (Open Knowledge Brasil). O Sentinela busca e processa automaticamente novas edições de diários oficiais de municípios alvo (ex: Nova Iguaçu), garantindo que o acervo esteja sempre atualizado sem intervenção humana.
2.  **Cura de Texto (Text Healing)**: Algoritmos regex que realizam uma cirurgia no texto extraído, reparando quebras de linha artificiais introduzidas por OCR ruim antes da indexação.
3.  **Law Scraper Estruturado (HTML Parsing)**: Para legislações online, o sistema preserva a hierarquia jurídica (Títulos > Capítulos > Artigos). Isso permite citações precisas ("Artigo 5º, Parágrafo Único").
4.  **Structured Data Ingestor (Planilhas)**: Processadores específicos para arquivos `.csv` e `.xlsx`, transformando linhas de dados em sentenças descritivas.
5.  **Vision AI Pipeline**: Fallback para PDFs digitalizados onde o Tesseract falha, acionando modelos multimodais para descrever tabelas ou layouts complexos.
6.  **Chunking Semântico Recursivo**: Fragmentação inteligente que respeita o contexto jurídico e gramatical.

#### B. Motor RAG (Retrieval-Augmented Generation)
1.  **Indexação**: Vetores armazenados no ChromaDB.
2.  **Recuperação**: Busca semântica pela "intenção" da pergunta.
3.  **Auditoria de Confiança (RAG Score)**: Cálculo matemático da proximidade entre o texto recuperado e a resposta gerada.

#### C. Gestão e Auditoria
*   **Editor de System Prompt via UI**: Ajuste fino da personalidade da IA em tempo real.
*   **Auditoria Imutável**: Logs com anonimização SHA256.

---

## 4. Filosofia: Privacidade e Justiça Epistêmica
1.  **Privacy by Design**: Nenhum dado deixa o servidor local.
2.  **Soberania Tecnológica**: Uso de modelos abertos e infraestrutura controlada pelo cidadão/instituição.

---

## 5. Conclusão
O Sentinela Cívico demonstra que a **Soberania da IA** é possível e acessível via **Vibe Coding**.

> *"A tecnologia deve ser uma sentinela da democracia, não uma caixa preta de terceiros."*
