# Relatório Fase 4: Engenharia de Prompt Jurídica e Hermenêutica (Sentinela) ⚖️

> **Foco**: A "Bússola Constitucional", Matriz de Decisão Kelseniana e Gestão de Conflitos.

Este relatório detalha como transformamos conceitos abstratos do Direito Constitucional em código Python e instruções de LLM. Enquanto a Fase 3 descreve *como* o sistema pensa, a Fase 4 define *quais regras* ele obedece.

## 1. A Bússola Constitucional (System Prompt)

O núcleo da "personalidade" jurídica do Sentinela reside no seu Prompt de Sistema (`sentinela_prompt_v2.md`).

### Axioma Hermenêutico
Definimos a **Constituição Federal** como a "Verdade Absoluta" (Truth Source).
*   **Regra de Ouro**: Se o cidadão pergunta sobre um Direito Fundamental (ex: Saúde, Educação), o sistema é instruído a afirmar o direito constitucional *antes* de citar burocracias locais.
*   **Corte Epistemológico**: *"Pare de buscar exceções se a Constituição garante o direito."* Essa instrução reduz respostas defensivas ou excessivamente burocráticas.

---

## 2. Matriz de Decisão Cognitiva (O "Cérebro" Jurídico) 🧠

Para navegar no caos legislativo brasileiro, o Sentinela aplica uma matriz de decisão rigorosa inspirada na Teoria Pura do Direito de Hans Kelsen. Esta matriz orienta o LLM na Fase 3 sobre qual norma prevalece em caso de conflito.

### Eixo A: Competência (Roteamento de Esfera)
O sistema verifica a origem da autoridade.
*   **Competência Suplementar**: Em temas de interesse local (ex: horário de silêncio, zoneamento urbano), a norma **Municipal** tem prevalência sobre normas gerais estaduais ou federais, salvo violação constitucional.

### Eixo B: Hierarquia (Pirâmide de Kelsen)
O LLM verifica o metadado `doc_type` para resolver antinomias verticais.
*   **Hierarquia Rígida**: Constituição > Lei Complementar > Lei Ordinária > Decreto > Portaria.
*   **Aplicação**: Um Decreto Municipal jamais pode revogar uma Lei Federal (exceto na competência específica mencionada acima).

### Eixo C: Temporalidade (Lex Posterior)
Para resolver antinomias horizontais (normas de mesmo nível), o sistema compara a `publication_date`.
*   **Lex Posterior Derogat Priori**: Lei posterior revoga lei anterior. O Sentinela explicita isso: *"Prevalece a Lei 123 de 2024 sobre a Lei 100 de 1990."*

---

## 3. Heurística Jurídica na Ingestão (`DocType`)

A inteligência jurídica começa antes da IA, no momento do upload (`src/interfaces/api/routes/upload.py`).

O sistema implementa um classificador determinístico para garantir a taxonomia correta:
1.  **Entrada**: Usuário seleciona categoria macro "Legislação".
2.  **Análise de Filename**: O código varre o nome do arquivo buscando palavras-chave de autoridade.
    *   *Se contém "Emenda"* -> Reclassifica como `emenda_constitucional`
    *   *Se contém "Complementar"* -> Reclassifica como `lei_complementar`
    *   *Se contém "Decreto"* -> Reclassifica como `decreto`
3.  **Resultado**: Quando esse documento chega ao RAG, o LLM sabe exatamente seu peso hierárquico (Eixo B) sem precisar "adivinhar" pelo texto.

---

## 4. Escuta Ativa Jurídica

A ambiguidade na linguagem natural frequentemente esconde conceitos jurídicos distintos.
*   *Usuário*: "Quero meu benefício."
*   *Ambiguidade*: Benefício Previdenciário (INSS/Federal) ou Benefício Social (CRAS/Municipal)?

O sistema recusa-se a responder (alucinar) e pergunta: *"Você se refere ao BPC/LOAS ou a algum auxílio municipal?"*. Isso garante segurança jurídica na orientação.

---

*Estado Atual: O Sentinela não apenas lê leis; ele entende o peso de cada palavra e a hierarquia de cada norma.*
