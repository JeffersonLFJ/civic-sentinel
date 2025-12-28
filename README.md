# Civic Sentinel 🛡️ (Sentinela)

Civic Sentinel é uma plataforma de monitoramento e auditoria de diários oficiais e documentos públicos, focada em transparência e justiça epistêmica algorítmica. O sistema utiliza técnicas avançadas de RAG (Retrieval-Augmented Generation), OCR e inteligência artificial local para processar e analisar dados governamentais.

## 🚀 Funcionalidades

### 🧠 Inteligência e Ingestão
- **Ingestão Híbrida Inteligente**: 
  - **Scan Local**: Monitoramento de pastas locais (`data/ingest`) com seleção manual de tipo de documento.
  - **PDFs "Curados"**: Algoritmo de *text healing* que corrige quebras de linha de OCR e fragmentação recursiva para leitura fluida.
  - **Diário Oficial**: Integração com API do Querido Diário para Niterói e Nova Iguaçu.
- **RAG Avançado**: Indexação vetorial (ChromaDB) com busca semântica de alta precisão.
- **OCR Robusto**: Falha graciosamente do Tesseract para estratégias visuais quando necessário.

### 🛡️ Auditoria e Controle
- **Painel Administrativo (`/admin`)**:
  - **Editor de System Prompt**: Interface visual para ajustar a personalidade e regras éticas da IA sem tocar em código (`⚙️ Prompt`).
  - **Auditoria Transparente**: Logs detalhados de cada interação, incluindo cálculo real de **Confiança (RAG Score)**.
  - **Limpeza de Dados**: Botões para limpar histórico de logs e reiniciar métricas.
- **Privacidade Radical**: Processamento 100% local com anonimização de usuários (SHA256).

## 🎮 Como Usar

### 1. Ingestão de Documentos
Você pode adicionar documentos de duas formas:
- **Upload Manual**: Botão `+ Upload Manual` no painel.
- **Scan Local**:
  1. Coloque arquivos na pasta `data/ingest`.
  2. Clique em `📁 Scan Pasta Local`.
  3. Selecione os arquivos e defina o tipo (Lei, Documento OCR, etc.).
  4. Clique em Confirmar.

### 2. Ajustando a IA
- Clique em **⚙️ Prompt** no topo da tela.
- Edite o texto para mudar como o Sentinela responde (ex: "Seja mais formal", "Cite sempre o artigo").
- Clique em Salvar. A mudança é imediata.

### 3. Verificando a Confiança
- Após uma resposta no Chat, abra o modal **📊 Status / Auditoria**.
- Verifique a coluna **Confiança**:
  - **0%**: A IA não encontrou base nos documentos (cuidado com alucinações).
  - **>70%**: Resposta fortemente embasada nos textos recuperados.

## 🛠️ Arquitetura

O projeto é dividido em camadas modulares:

- `src/core`: Gestão de banco de dados (SQLite + ChromaDB).
- `src/ingestors`: Componentes para captura de dados externos e locais.
- `src/ocr`: Processamento de imagem para texto.
- `src/reasoning`: Lógica de classificação e filtragem (Bioética, Alertas).
- `src/interfaces/api`: API REST robusta construída com FastAPI.

## 📋 Pré-requisitos

- Python 3.10+
- [Ollama](https://ollama.ai/) rodando localmente (modelo `gemma3:27b`).
- Tesseract OCR instalado no sistema.
- Docker (opcional, para implantação em container).

## ⚙️ Instalação e Setup

1. **Clone o repositório**:
   ```bash
   git clone https://github.com/JeffersonLFJ/civic-sentinel.git
   cd civic-sentinel
   ```

2. **Crie e ative o ambiente virtual**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # No Windows: venv\Scripts\activate
   ```

3. **Instale as dependências**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configuração**:
   Crie um arquivo `.env` na raiz (baseado nas configurações em `src/config.py`) se precisar customizar portas ou caminhos.

5. **Inicie a API**:
   ```bash
   python -m src.interfaces.api.main
   ```

## 🐳 Docker

Para rodar via Docker Compose:
```bash
docker-compose up --build
```

## ⚖️ Compromissos Bioéticos (Privacy by Design)

O Sentinela implementa restrições técnicas invioláveis baseadas na tese de Justiça Epistêmica:
1.  **Anonimato Radical**: Nenhum dado pessoal cru é persistido; identificadores são convertidos via SHA256 antes do processamento.
2.  **Soberania Tecnológica**: Dependência zero de Big Techs. Todo o processamento (OCR e LLM) ocorre *on-premise*.
3.  **Auditabilidade**: Cada inferência da IA carrega metadados de confiança e versão do prompt utilizado.

## 📄 Licença

Este projeto está licenciado sob a **Mozilla Public License 2.0 (MPL 2.0)**. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---
Desenvolvido por **Jefferson Lopes** via **Vibe Coding** 🎧
Utilizando a CLI **Google AntiGravity** e modelos **Gemini 3 High & Flash**.

Foco em **Transparência e Justiça Social**.
