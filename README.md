# Sentinela Cívico 🛡️

![Status](https://img.shields.io/badge/Status-Operacional-green) ![IA](https://img.shields.io/badge/IA-Local-blue) ![Versão](https://img.shields.io/badge/v-1.1-orange)

> **Monitoramento legislativo soberano com Inteligência Artificial.**

O Sentinela Cívico é uma plataforma que "lê" diariamente o Diário Oficial do seu município, entende o contexto das leis e licitações, e permite que qualquer cidadão converse com esses documentos de forma natural, como se estivesse falando com um especialista jurídico.

---

## 🙋‍♀️ Para Leigos: Como Rodar (Guia Rápido)

Se você não é programador, siga este passo a passo para colocar o Sentinela para rodar no seu computador (Windows, Mac ou Linux).

### O que você precisa antes:
1.  **Ollama**: Baixe e instale em [ollama.ai](https://ollama.ai).
    *   Abra seu terminal e rode: `ollama run gemma3:27b` (Isso vai baixar o "cérebro" da IA, pode demorar).
2.  **Python**: Tenha o Python 3.10 ou superior instalado.
3.  **Git**: Para baixar o código.

### Passo a Passo:

1.  **Baixe o Sentinela**:
    Abra seu Terminal (ou CMD) e cole:
    ```bash
    git clone https://github.com/JeffersonLFJ/civic-sentinel.git
    cd civic-sentinel
    ```

2.  **Instale as dependências** (faça isso só na primeira vez):
    ```bash
    # Cria um ambiente isolado para não bagunçar seu PC
    python3 -m venv venv
    
    # Ativa o ambiente (Mac/Linux)
    source venv/bin/activate
    # Se for Windows, use: venv\Scripts\activate
    
    # Instala as ferramentas necessárias
    pip install -r requirements.txt
    ```

3.  **Rode o sistema**:
    ```bash
    python -m src.interfaces.api.main
    ```

4.  **Use**:
    Abra seu navegador em [http://localhost:8000/docs](http://localhost:8000/docs) (para testar a API) ou acesse o Frontend (se configurado na porta padrão).

---

## 🎓 Relatório Técnico & Acadêmico

Este projeto serve como prova de conceito para **Soberania Digital** e **Justiça Epistêmica** aplicadas à tecnologia cívica. Abaixo, detalhamos o funcionamento interno, diferenciais e a filosofia de desenvolvimento.

### 1. O Que o Sentinela Faz?
O sistema opera em um ciclo contínuo de **Vigilância** e **Disponibilização**:
1.  **Ingestão**: Conecta-se à API do *Querido Diário* (Open Knowledge Brasil) ou monitora pastas locais.
2.  **Processamento Adaptativo (Selecionado pelo Usuário)**:
    O comportamento da IA muda conforme a categoria de documento que o usuário define no upload:
    *   **Diário Oficial**: Aplica OCR especializado em múltiplas colunas.
    *   **Lei (HTML)**: Processa leis em formato web preservando estrutura nativa (tags HTML).
    *   **Lei (PDF)**: Aplica OCR e depois fragmenta o texto usando o "Stateful Splitter" para reconstruir a hierarquia (Artigo > Inciso).
    *   **Foto Denúncia**: Ignora OCR e usa **Gemma Vision** para "olhar" a imagem e descrever o problema (ex: "buraco na via", "lixo acumulado").
    *   **Documento Padrão**: Usa Tesseract para extração direta de texto, em caso de baixa confiabilidade usa o **Gemma Vision** para "ler" o pdf ou imagem.

3.  **Indexação Híbrida & Chunking Especializado**:
    A forma como o texto é "fatiado" (chunking) para o banco de dados também varia para maximizar o entendimento:
    *   **Legislação**: Usa um *Stateful Splitter* exclusivo que preserva a hierarquia. Um chunk com o texto "Art. 5º" carrega invisivelmente o contexto "Lei 1234 > Capítulo I > Seção II", garantindo que a IA nunca perca a referência.
    *   **Texto Geral**: Usa quebra semântica por parágrafos.
    *   **Orçamentos**: (Em breve) Preservação de estruturas tabulares.
    
    Os dados são então salvos simultaneamente em ChromaDB (Busca de Conceitos) e SQLite FTS5 (Busca de Palavras Exatas).
4.  **Recuperação (RAG)**: Quando o usuário pergunta, o sistema recupera os trechos mais relevantes para responder com base em fatos.

### 2. Novas Tecnologias (v1.1)

#### 🧠 HyDE (Hypothetical Document Embeddings)
Os cidadãos raramente usam termos técnicos. Em vez de perguntar *"Qual o decreto do artigo 5º?"*, eles perguntam *"O posto de saúde fecha cedo?"*.
O **HyDE** resolve isso com uma técnica de "Alucinação Controlada":
1.  O usuário pergunta.
2.  O Sentinela pede para a IA: *"Escreva uma resposta hipotética judicial para essa pergunta."*.
3.  A IA gera um texto cheio de termos técnicos (*"Conforme portaria municipal de regulação ambulatorial..."*).
4.  Usamos esse texto técnico para buscar os documentos reais.
**Resultado**: O sistema entende a *intenção*, não apenas as palavras.

#### 🔍 Busca Híbrida & Re-ranking
Para garantir precisão absoluta, o Sentinela agora usa uma estratégia tripla:
1.  **Busca Semântica (ChromaDB)**: Encontra conceitos (ex: "corrupção" pode trazer textos sobre "desvio de verba").
2.  **Busca Logística (SQLite FTS5)**: Encontra palavras exatas (ex: "Lei 8.666").
3.  **Cross-Encoder (Re-ranker)**: Um "segundo cérebro" lê os top-20 resultados de ambos os métodos e reordena os 5 melhores para entregar ao usuário.

### 3. Detalhes Técnicos de Processamento

#### 🧹 Limpeza de HTML (Lei Web)
Para leis importadas via HTML, utilizamos a biblioteca **BeautifulSoup4** para fazer uma "faxina" rigorosa antes que o texto toque no LLM.
*   **Tags são preservadas? Não.** Tags HTML (`<div>`, `<span>`) são REMOVIDAS. Para o processador, elas são ruído.
*   **O que fica?** Extraímos apenas o texto puro, mas nossa lógica **reconstrói a estrutura** visualmente usando quebras de linha e indentação, para que a IA entenda onde começa e termina um parágrafo ou inciso.
*   **Scripts e Menus**: Elementos de navegação, scripts e estilos são removidos cirurgicamente.

#### 🥩 Estratégia de Chunking (Fatiamento)
O tamanho do "pedaço" de texto que a IA lê varia para otimizar o contexto:

1.  **Documentos Gerais (Padrão)**
    *   **Método**: Divisão Recursiva Semântica.
    *   **Tamanho Alvo**: ~1500 caracteres (aprox. 300 palavras).
    *   **Sobreposição**: Não fixa. O algoritmo prioriza quebras naturais.

2.  **Diário Oficial (Leitura Contínua)**
    *   **Método**: Janela Deslizante (*Sliding Window*).
    *   **Tamanho**: 3000 caracteres.
    *   **Sobreposição**: 500 caracteres.

3.  **Legislação (Hierárquico)**
    *   **Método**: *Stateful Splitter*.
    *   **Contexto**: Injeção invisível de metadados (Lei > Artigo) em cada pedaço.

#### 🏗️ Componentes de Bastidor (O que você não vê)
*   **Classificador de Urgência (`alert_classifier.py`)**: Este módulo atua como uma "triagem de pronto-socorro". Ao receber um documento, ele verifica instantaneamente a presença de termos críticos (heurística de *Fast Path*):
    *   🔴 **Alta Urgência**: "Risco de vida", "Emergência", "Calamidade", "Desvio".
    *   🟡 **Média Urgência**: "Irregularidade", "Suspeita", "Atraso".
    *   🟢 **Baixa Urgência**: Texto informativo padrão.
    *   *Nota*: Essa etiqueta é gravada nos metadados do documento, permitindo que a IA filtre respostas focando primeiro no que é crítico.
*   **Auto-Manutenção (`maintenance.py`)**: Um "gari digital" que roda periodicamente para apagar arquivos temporários de upload (mais de 24h) e manter o disco limpo.
*   **Download Sob Demanda**: Na primeira execução, o Sentinela baixa automaticamente os modelos de IA (Cross-Encoder) necessários. Não se assuste se demorar um pouco!


#### 🕵️‍♂️ Privacidade Blindada (Anonimato Real)
O Sentinela leva o anonimato a sério. Não confiamos apenas na boa vontade; forçamos a privacidade via código:
*   **PII Scrubber (O "Censor" Ético)**: Antes de qualquer mensagem chegar à IA, um filtro intercepta e remove dados sensíveis.
    *   **Remove**: CPFs, E-mails, Telefones e **Redes Sociais** (Links de Instagram/Facebook e handles `@usuario`).
    *   *Resultado*: O banco de dados vê apenas `[DADO_REMOVIDO]`.
*   **Fingerprint de Dispositivo**: Substituímos logins tradicionais por uma assinatura digital única do dispositivo. Sabemos que *é você* (para manter o histórico), mas matematicamente não conseguimos saber *quem* é você.

#### ✨ "Vibe Coding" (Simbiose Humano-IA)
Este projeto não foi programado da forma tradicional. Ele foi desenvolvido através da metodologia de **Vibe Coding**:
- **Humano**: Jefferson Lopes (Direção Criativa, Ética e Regras de Negócio).
- **Co-Piloto**: Google Gemini 3 (High & Flash) via **Google AntiGravity CLI**.
- **Processo**: Desenvolvimento acelerado focado na *intenção* do código, onde a IA atua como um par programador de alta frequência, implementando a arquitetura sob supervisão humana rigorosa.

#### 🛡️ Soberania Digital
Em tempos de capitalismo de vigilância, o Sentinela adota uma postura radical:
- **Local-First**: Nada é enviado para a nuvem da OpenAI, Google ou Microsoft. O modelo de linguagem (`Gemma 3`) roda no computador do usuário.
- **Dados Sensíveis**: Informações municipais e logs de auditoria nunca saem da infraestrutura da prefeitura ou do cidadão.

#### ⚖️ Bioética e Segurança
O Sentinela implementa restrições técnicas invioláveis baseadas na tese de Justiça Epistêmica:
1.  **Anonimato Radical (Privacy by Design)**: Nenhum dado pessoal cru é persistido. Identificadores são hashes SHA256 e **redes sociais são banidas** dos logs.
2.  **Auditabilidade**: Cada inferência da IA carrega metadados de confiança e versão do prompt utilizado.
*   **Log de Auditoria**: Cada resposta gerada pela IA é gravada com um "Score de Confiança". Se a IA não tiver certeza, o sistema avisa.
*   **Filtros de Viés**: Módulos (em desenvolvimento) para detectar e bloquear respostas que violem justiça epistêmica ou amplifiquem preconceitos.

---

## 🛠️ Stack Tecnológica

*   **Linguagem**: Python 3.10+
*   **API**: FastAPI (Assíncrono)
*   **Banco Vetorial**: ChromaDB (Persistente)
*   **Banco Relacional**: SQLite + FTS5 (Full Text Search)
*   **LLM**: Ollama (Interface) + Gemma 3 (Modelo)
*   **Ingestão**: HTTPX (Async) + Tesseract OCR

---

## 📄 Licença

Este projeto é de código aberto sob a licença **Mozilla Public License 2.0**.
Desenvolvido com ❤️ e 🤖 para a transparência pública.
