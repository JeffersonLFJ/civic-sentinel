# Relatório Fase 2: Banco de Dados e Recuperação (Sentinela) 🗄️

> **Foco**: Arquitetura Híbrida, Recuperação Contextual (RAG) e "Busca por Intenção (Keywords)".

Este relatório detalha como o Sentinela organiza e recupera informações. O sistema foi projetado para ser preciso (encontrar a lei exata) e inteligente (entender o que o cidadão quis dizer).

## 1. Arquitetura de Banco de Dados Híbrida

Diferente de sistemas simples, o Sentinela utiliza dois bancos de dados trabalhando em harmonia:

1.  **ChromaDB (Banco Vetorial - "O Cérebro")**:
    *   **Função**: Armazena o "significado" (embedding) dos pedaços de texto.
    *   **Poder**: Permite buscas semânticas (vizinhos mais próximos).
2.  **SQLite + FTS5 (Banco Relacional - "A Bibliotecária")**:
    *   **Função**: Busca por palavras-chave exatas e metadados.
    *   **Poder**: Ideal para termos técnicos como "Lei 12.345" ou "Artigo 5º".

---

## 2. A "Mágica" da Recuperação (Do "Loud car" à Lei) 🔍

O usuário perguntou: *"Um carro de som está na minha rua com um som muito alto."*

### Estágio 1: Extração de Intenção e Palavras-Chave 🗝️
Antes de buscar, um "Motor de Raciocínio" (`interpret_intent`) realiza uma chamada silenciosa ao LLM para estruturar a demanda.

*   **Extração de Keywords**: O modelo não gera apenas uma frase, ele extrai uma **lista de 3 a 5 palavras-chave** (ex: `["som", "automotivo", "perturbação"]`). Isso permite que a busca textual use lógica **OR**, encontrando documentos que contenham qualquer um dos termos, aumentando drasticamente a cobertura.
*   **Identificação de Esfera (Lazy Filtering)**:
    *   Temas de **Competência Concorrente** (Meio Ambiente, Saúde) retornam sphere `unknown`, acionando busca em todas as esferas.
    *   Restrição para `municipal` apenas se explícita ("em Nova Iguaçu").

### Estágio 2: Busca Híbrida (Wide Net)
O sistema dispara buscas simultâneas:
*   **Busca Vetorial (ChromaDB)**: 50 candidatos (Top-K configurável).
*   **Busca por Palavra-Chave (SQLite)**: 50 candidatos filtrados pela esfera detectada.
    *   **Mecanismo**: Usa a lista de keywords (`MATCH 'termo1 OR termo2 OR termo3'`) para garantir que variações de vocabulário não impeçam a recuperação.

*Nota: O mecanismo HyDE (Hypothetical Document Embeddings) foi desativado temporariamente em favor da estratégia de Keywords OR, que se mostrou mais robusta para termos jurídicos exatos.*

---

## 3. Pipeline de Reranking e Expansão (O Refino) ⚡

Após coletar os candidatos, o sistema faz uma triagem rigorosa para integrar com o raciocínio:

1.  **Deduplicação**: Remove fragmentos repetidos via Hash MD5.
2.  **Re-ranking (Cross-Encoder)**: O modelo neural **`cross-encoder/ms-marco-MiniLM-L-6-v2`** lê a pergunta original e cada documento candidato em pares, atribuindo uma nota de 0 a 1 de relevância real.
3.  **Expansão de Contexto (Parent Retrieval)**:
    *   O sistema não entrega apenas o fragmento (chunk). Ele busca no `doc_parents` o contexto superior: o **Artigo completo**, a **Página do Diário Oficial** ou as **50 linhas adjacentes** no caso de Tabelas Orçamentárias.

---

## 4. Integração com o Raciocínio (Fase 3) 🧠

Esta estrutura de dados alimenta o Fluxo de Decisão. O filtro de esfera relaxado na Fase 2 permite que documentos conflitantes (ex: Lei Federal vs Municipal) cheguem à Fase 3, onde a hierarquia de Kelsen será aplicada para decidir a prevalência.

---

*Estado Atual: O sistema recupera contexto amplo via Keywords OR e Vetores, pronto para a análise hermenêutica da Fase 3.*
