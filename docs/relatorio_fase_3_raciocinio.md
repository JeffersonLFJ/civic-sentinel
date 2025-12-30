# Relatório Fase 3: Raciocínio e Cognição (Sentinela) 🧠

> **Foco**: Fluxo Integrado, Escuta Ativa e Conectividade.

Este relatório detalha a "Mente" do Sentinela. Após recuperar os documentos na Fase 2, o sistema precisa "ler", "julgar" e "responder". Aqui ocorre a orquestração do pensamento.

## 1. Fluxo de Raciocínio Integrado (Pipeline Cognitivo) 🧩

O raciocínio não acontece no vácuo. Ele é o passo final de uma cadeia de 8 estágios desenhada para garantir que o LLM (Gemma 3) nunca "alucine", mas trabalhe apenas com fatos.

### O Pipeline de 8 Passos
1.  **Input do Cidadão**: Entrada em linguagem natural ("Carro de som alto na rua").
2.  **Qualificação (Gemma - Camada de Intenção)**:
    *   **Intenção Real**: O LLM traduz "carro de som" para "perturbação do sossego".
    *   **Keywords**: Extrai **3 a 5 palavras-chave** (ex: `["som", "automotivo", "lei"]`) para busca robusta.
    *   **Ambiguidade**: Calcula um score de dúvida (0.0 a 1.0).
3.  **Filtro de Ambiguidade (Escuta Ativa)**: Se o score for alto, o sistema **para** e pede clareza ao usuário (ex: "Você fala de Banco (dinheiro) ou Banco (assento)?").
4.  **Recuperação Híbrida (Wide Net)**: Busca 50 itens por Vetor + 50 por Palavras-Chave (OR Logic).
5.  **Deduplicação**: Limpeza de redundâncias via hash MD5.
6.  **Curadoria (MiniLM)**: O Cross-Encoder re-lê os 100 candidatos e escolhe os Top-5 mais relevantes.
7.  **Expansão de Contexto**: Recupera o artigo ou página original completa dos vencedores.
8.  **Raciocínio Final (Gemma)**: O modelo recebe o "Sanduíche de Contexto" para gerar a resposta.

---

## 2. Estrutura de Prompt Dinâmico (Passo 8) 📝

A "Mágica" do raciocínio está na montagem do prompt final que é enviado ao LLM. Não é apenas uma pergunta, é um dossiê estruturado:

1.  **System Prompt**: A "Personalidade Jurídica" (Detalhada na **Fase 4**).
2.  **Contexto Recuperado**: Os documentos que venceram o funil da Fase 2, com seus metadados de score e tipo.
3.  **Histórico**: A conversa atual.

Isso garante que o modelo atue como um **Consultor Jurídico Consultando um Vade Mecum**.

---

## 3. Matriz de Decisão Cognitiva (Link) 🔗

A lógica pesada de decisão (Pirâmide de Kelsen, Competência Federativa e Temporalidade) foi movida para o **[Relatório Fase 4: Aspectos Jurídicos](file:///Users/jeffersonlopes/.gemini/antigravity/brain/8cd4ea72-05e2-48c6-a5c9-4305711b25b2/relatorio_fase_4_juridico.md)**, pois trata-se das *regras* do pensamento, não apenas do *fluxo*.

Lá explicamos como o sistema decide que uma Lei Municipal vence uma Federal em assuntos locais, ou como uma Lei Nova revoga uma Velha.

---

## 4. Conectividade Premium (UX) ✨

A camada cognitiva se conecta ao frontend via **Server-Sent Events (SSE)**.
*   **Fluxo Contínuo**: A resposta é gerada token-a-token.
*   **Citações Precisas**: O fluxo retorna primeiro os metadados (fontes), permitindo que a interface monte os "cards de citação" visualmente antes mesmo do texto aparecer.

---

*Estado Atual: O sistema processa informação jurídica com rigor acadêmico, apoiado por uma pipeline de dados robusta.*
