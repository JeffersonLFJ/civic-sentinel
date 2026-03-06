# Arquitetura de Ingestão e Processamento do Sentinela

Este documento detalha o ciclo de vida de um arquivo no Sentinela, desde o momento do *upload* até se tornar fragmentos pesquisáveis (chunks) nos bancos de dados do RAG.

---

## 1. Roteamento de Ingestão (`router.py`)

Quando o usuário faz o upload de um arquivo via frontend, ele obrigatoriamente escolhe o `DocType` (tipo do documento). O `IngestionRouter` no backend intercepta essa chamada e direciona o arquivo para o pipeline mais otimizado.

*   `legislacao`: Leis, Decretos, Constituição. Se o formato for `.html` (comum no Planalto.gov/Alerj), ativa-se o `LawScraper` para limpar as tags HTML sujas. Se for `.pdf`, usa-se o `Docling` para manter o layout intocado.
*   `tabela`: Arquivos `.csv` ou `.xlsx`. O sistema lê os dados via biblioteca `pandas` e converte instantaneamente as colunas para formato Markdown (`| Coluna |...`), otimizando drasticamente o entendimento do LLM.
*   `diario`: Diários Oficiais. Vai direto para o `Docling`, pois é o extrator que melhor lida com colunas duplas e caixas de texto separadas.
*   `documento`: Textos livres ou PDFs gerais de domínio público/denúncia.

---

## 2. O Papel do OCR (Tesseract e Gemma Vision)

O mecanismo de Extração Ótica de Caracteres (OCR) é o último recurso em caso de imagens puras ou PDFs xerocados sem camada de texto.

**O Tesseract ainda está em uso? SIM!**
Se você observar o arquivo `src/ocr/tesseract_processor.py`, ele permanece ativo no ecossistema e é uma parte valiosa.
O fluxo de decisão de OCR ocorre da seguinte forma:

1.  A primeira tentativa para PDFs e Documentos Gerais é sempre via extrator nativo inteligente (**Docling** / IBM).
2.  Se o Docling falhar, ou extrair menos de **50 caracteres** (indício claro de um PDF xerocado), o Roteador assume a falha.
3.  Diante dessa falha, o sistema aciona o `ocr_engine`. Se for uma imagem (ex: foto de uma denúncia ambiental, `.jpg`), o sistema delega para o modelo visual avançado **Gemma Vision Fallback** caso configurado, ou para o legado **Tesseract (PyTesseract)**.
4.  O Tesseract quebra imagens grandes em páginas individuais via `pdf2image` e lê as caixas de texto com baixa precisão semântica (apenas converte pixels em letras), mas ainda garantindo que o dado não seja perdido.

---

## 3. Estratégias de Fatiamento (Chunking) (`text_processing.py`)

Colocar um Diário Oficial inteiro na memória do LLM estouraria os limites da máquina. O arquivo fatiador inteligente (`SmartTextSplitter`) usa abordagens sob medida para não quebrar contextos importantes no meio:

### 3.1. Fatiamento de Leis (`split_by_law_articles`)
*(Extremamente Crítico para o contexto Jurídico)*
O algoritmo **NUNCA** corta uma frase ao meio por limite de limite de bytes genérico.
1. O regex procura o início de cada parágrafo com as palavras reservadas `"Art. \dº"`.
2. O sistema acompanha e "memoriza" os títulos-mãe. Exemplo: Ele sabe que está dentro do `LIVRO 1 > TÍTULO 2 > CAPÍTULO 3`.
3. Todo fatiamento é forçado a ter esse título enxertado no topo do próprio texto (`[LIVRO 1 > TÍTULO 2] Art 5º...`), garantindo que o LLM não leia o artigo de forma descontextualizada.
4. **Sub-divisão profunda:** Se um único artigo for excepcionalmente massivo (mais de 2500 letras), o algoritmo aciona uma sub-divisão por `"§" (Parágrafos)` ou por Números Romanos `"I - " (Incisos)`.

### 3.2. Fatiamento Semântico para Textos Gerais (`split_semantically`)
Textos corridos sem padronização são submetidos a um modelo neural menor (Sentence Transformer `all-MiniLM-L6`). 
1. O texto é quebrado por pontos-finais.
2. O modelo transforma janelas de frases em vetores matemáticos e mede a "semelhança" geométrica entre eles.
3. O software encontra os Vales Estatísticos: lugares pontuais onde a frase 1 não tem absolutamente nada a ver matematicamente com a frase 2, significando uma quebra de assunto real. O "corte de tesoura" só ocorre nesses vales.

### 3.3. Tabela Header Persistente (`split_markdown_table`)
Caso planilhas gigantes com centenas de linhas passem pelo fatiador, o cabeçalho original (`Nome | Idade | Endereço`) é repetido e forçado manualmente no topo de toda fatia filha. Sem isso, a fatia seria apenas de números vazios e perderia por completo a chance de ser recuperada depois.

---

## 4. O Sistema de Dados Híbrido

Uma vez que o longo PDF original virou dezenas de recortes (`chunks`) injetados de contextos de capítulo/artigo, os dados seguem em paralelo para duas tecnologias distintas:

> [!TIP]
> **ChromaDB (Banco de Dados Vetorial)**
> Especialista em Busca por Sentido/Vibe. Os trechos de texto são reduzidos matematicamente a números (Embeddings) de novo. Quando o cidadão pergunta "Direitos das gestantes com asfalto perto da rocinha", o ChromaDB faz trigonometria para achar o conjunto de palavras que fica mais perto no espaço matemático (Mesmo que não use essas palavras).

> [!CAUTION]
> **SQLite FTS5 (Banco de Dados Relacional - Full Text Search)**
> O SQLite em paralelo cria um Dicionário Reverso (Keywords). É uma lista telefônica crua da estrutura lexical. Impede a cegueira vetorial, recuperando com precisão de 100% palavras incomuns que a trigonometria acima mataria de imediato, como o número de portaria `Decreto nº 42.143`.

---

### Resumo do RAG Atual
A Ingestão divide inteligentemente, e a Conversa do usuário faz dois tiros simultâneos (*ChromaDB* e *SQLite*) retornando na pior das hipóteses até 20 documentos por pesquisa. No final do fluxo, o Sentinela utiliza um roteador "Re-Ranker" cruzado (Cross Encoder) listado como `ms-marco-MiniLM` para jogar os documentos contra as paredes. Só os 5 que vencerem a arena de relevância são despachados para o Gigante LLM de Resumo (Gemma 3) ler.
