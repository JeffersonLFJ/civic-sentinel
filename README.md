# Civic Sentinel 🛡️ (Sentinela)

Civic Sentinel é uma plataforma de monitoramento e auditoria de diários oficiais e documentos públicos, focada em transparência e justiça epistêmica algorítmica. O sistema utiliza técnicas avançadas de RAG (Retrieval-Augmented Generation), OCR e inteligência artificial local para processar e analisar dados governamentais.

## 🚀 Funcionalidades

- **Ingestão Inteligente**: Monitoramento automático de diários oficiais (ex: Nova Iguaçu via Querido Diário) e pastas locais.
- **OCR Robusto**: Processamento de documentos digitalizados usando Tesseract com validação de confiança.
- **Cérebro RAG**: Indexação semântica em ChromaDB e busca vetorial para contextos precisos.
- **Privacidade**: Processamento local utilizando Ollama (Gemma 3:27B) para garantir a segurança dos dados.
- **Auditoria**: Trilha completa de ações com scores de confiança.
- **Interface Admin**: Dashboard para visualização de logs, documentos citados e métricas.

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
