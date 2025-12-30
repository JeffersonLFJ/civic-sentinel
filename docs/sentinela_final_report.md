# 🦅 Sentinela: Relatório Geral do Sistema
> **Arquitetura de Inteligência Cívica e Jurídica**

O **Sentinela** é uma plataforma de IA projetada para monitorar, interpretar e democratizar o acesso a documentos oficiais (Diários Oficiais, Leis e Normas). Diferente de um RAG genérico, ele opera sob rígidos axiomas de **Hermenêutica Jurídica** e **Soberania de Dados**.

Este documento serve como índice mestre para a documentação técnica do projeto.

---

## 📚 Índice de Relatórios (Fase a Fase)

A construção do sistema foi dividida em 6 camadas de engenharia:

### [Fase 1: Ingestão e Estrutura](relatorio_fase_1_ingestao.md) 🧱
*   **Foco**: Como o dado entra.
*   **Destaques**: Auto-Dispatch (HTML vs PDF), Estratégia de Fragmentação (Macro/Micro) e Preservação de Hierarquia.

### [Fase 2: O Banco de Dados Híbrido](relatorio_fase_2_dados.md) 💾
*   **Foco**: Como o dado é guardado e encontrado.
*   **Destaques**: Busca Híbrida (Keywords FTS5 + Vetores Chroma), Reranking Cross-Encoder e exclusão da busca "cega" (HyDE Desativado).

### [Fase 3: O Fluxo de Raciocínio](relatorio_fase_3_raciocinio.md) 🧠
*   **Foco**: Como a IA pensa.
*   **Destaques**: Extração de Intenção, interpretação de Keywords e Escuta Ativa (desambiguação antes da busca).

### [Fase 4: Engenharia de Prompt Jurídica](relatorio_fase_4_juridico.md) ⚖️
*   **Foco**: As regras que a IA obedece (O "Caráter").
*   **Destaques**: Matriz de Decisão Kelseniana (Hierarquia), Eixos de Competência (Federal/Est/Mun) e Temporalidade (*Lex Posterior*).

### [Fase 5: Validação e Controle](relatorio_fase_5_validacao.md) 🛡️
*   **Foco**: Governança de Metadados.
*   **Destaques**: Interface de Quarentena (Staging), validação humana obrigatória de metadados e controle de parâmetros do cérebro (`/settings`).

### [Fase 6: Diagnósticos e Auditoria](relatorio_fase_6_diagnosticos.md) 🩺
*   **Foco**: Saúde do Sistema.
*   **Destaques**: Auditoria de Raciocínio (Raio-X), Logs de Confiança e testes (Manual/Automatizado).

---

## 🚀 Arquitetura em Uma Frase

> "Um pipeline de ingestão multibimodal alimenta um banco híbrido, governado por uma matriz de decisão constitucional, validado por humanos em quarentena e auditado em tempo real."

---

## 🏁 Próximos Passos (Roadmap Futuro)
*   **Expansão Federativa**: Adicionar suporte nativo a Diários de outros estados.
*   **Agentes Autônomos**: Criar "agentes de alerta" que notificam usuários sobre novos temas (ex: "Nova lei sobre dengue publicada").

---
*Documentação gerada automaticamente pela IA Antigravity.*
