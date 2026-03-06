# Fatiador Dinâmico de Prompts (Prompt Slicer)

O sistema Sentinela passou a utilizar o **Fatiador Dinâmico de Prompts** (localizado em `src/core/prompt_builder.py`) para montar as instruções do LLM (System Prompt) de forma modular. 

Historicamente, um único arquivo longo de regras (`sentinela_prompt_v2.md`) era enviado para a inteligência artificial a cada interação. Isso causava o problema da **"Janela de Contexto Saturada"**, onde regras rígidas de interpretação jurídica e orientações restritas poluíam a IA e enviesavam respostas comuns do dia-a-dia, fazendo-a reagir a saudações ou bate-papos com tom demasiadamente técnico.

## Como Funciona

Em vez de empurrar todo o texto, o backend constrói o prompt como blocos de montar (Lego), adicionando módulos baseados na **intenção do usuário** (capturada pelo LLM minúsculo de extração de inteção).

O fatiamento reconhece os cabeçalhos (`###`) do arquivo `sentinela_prompt_v2.md` como divisores lógicos. 

### Blocos Modulares e Critérios de Injeção:

1. **IDENTIDADE & PERSONALIDADE:**
   - **Gatilho:** Sempre carregado.
   - **Motivo:** A IA deve sempre lembrar sua "persona" original (educada, focada em Tinguá, objetiva).

2. **GESTÃO DE CONVERSA:**
   - **Gatilho:** Sempre carregado.
   - **Motivo:** Orientações sobre tratar xingamentos de forma neutra e não exibir tags de debug na resposta final.

3. **INSTRUÇÕES DE RAG:**
   - **Gatilho:** Só injetado quando a variável `search_needed=True` (ou quando existem documentos no contexto).
   - **Motivo:** Se o usuário apenas cumprimenta ("Olá"), não é preciso advertir a IA severamente sobre alucinar citações e fontes, pois não há pesquisa nessa mensagem.

4. **MATRIZ DE DECISÃO (BÚSSOLA CONSTITUCIONAL):**
   - **Gatilho:** Só injetado caso a intenção detecte uma "esfera" estatal (`federal`, `estadual`, `municipal`) OU a pesquisa recupere documentos tipo leis/decretos.
   - **Motivo:** É o bloco mais pesado do prompt (Hierarquia de Kelsen). Forçar a análise constitucional em conversas comuns gerava alucinações onde a IA tentava aplicar a lei a assuntos banais.

5. **MÓDULO DE IMAGINAÇÃO CÍVICA:**
   - **Gatilho:** Só injetado quando as palavras-chave indicam termos proativos/estipulativos (ex: "imagina", "simula").
   - **Motivo:** Evita que a IA seja passiva caso o usuário solicite um cenário fictício.

6. **BLOCO DE NOTAS (SCRATCHPAD) E SEGURANÇA:**
   - **Gatilho:** Sempre carregado.
   - **Motivo:** O Scratchpad mantém a capacidade de registrar "memórias" de curto prazo na sessão atual do navegador `<SCRATCHPAD>nome, dados cruciais</SCRATCHPAD>`. Segurança impede vazamento de PII (anonimização de dados pessoais sensíveis).

## Vantagens
- Economia de Tokens (custo x hardware).
- Menor confusão cognitiva da IA em mensagens de follow-up.
- As respostas se dão num tom muito mais humano, ágil e flexível para diálogos despretensiosos.
