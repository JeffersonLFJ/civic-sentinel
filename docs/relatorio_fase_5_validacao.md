# Relatório Fase 5: Validação, Governança e Controle 🛡️

> **Foco**: Quarentena de Metadados, Privacidade e Painel de Controle ("Brain Settings").

Este relatório detalha os mecanismos que garantem a **qualidade do dado** que entra e a **segurança** da configuração que opera o sistema.

## 1. O Protocolo de Quarentena (Staging de Metadados) 🚧

Diferente de sistemas RAG comuns que indexam tudo cegamente, o Sentinela opera com um princípio de **Governança Prévia**. A quarentena não é apenas para verificar se o OCR funcionou, mas puramente para garantir a **integridade jurídica** do documento.

### O Fluxo de Validação
1.  **Entrada**: Todo documento (Upload ou Scan Local) nasce com status `pending`. O LLM é "cego" para ele.
2.  **Auditoria Humana**: O administrador acessa a Área de Staging (`/admin/staging`).
3.  **Checklist de Metadados (Obrigatório)**:
    *   **Título**: O nome do arquivo está descritivo? (ex: "lei_123.pdf" vs "Lei Complementar 123 - Zoneamento").
    *   **Esfera**: O documento está classificado na esfera correta (Municipal/Federal)? Isso impacta diretamente na *Matriz de Decisão Kelseniana*.
    *   **Data**: A data de publicação está correta? (Crucial para o critério de *Lex Posterior*).
    *   **Tipo**: É Lei, Decreto ou Portaria? (Crucial para *Hierarquia*).
4.  **Aprovação**: Somente após validar esses campos o admin clica em "Aprovar".
    *   *Efeito*: O sistema dispara a indexação no ChromaDB e altera o status para `active`.

**Benefício**: Evita a "poluição semântica" e garante que a Inteligência Jurídica tenha substrato confiável para trabalhar.

---

## 2. Gestão de Parâmetros e Configuração (O Painel de Controle) ⚙️

O Sentinela não é uma "caixa preta". Todas as variáveis cognitivas e comportamentais são expostas em uma interface administrativa dedicada (`/admin/settings`).

### Painel "Brain Settings"
Reunimos todos os ajustes neurais em uma única tela, permitindo calibração em tempo real sem deploy de código:

1.  **Temperatura Criativa (0.0 - 1.0)**:
    *   Controla a "imaginação" do modelo.
    *   *Default*: `0.1` (Rigor Jurídico).
    *   *Configurável*: Pode ser aumentado para `0.7` se o objetivo for brainstorming de políticas públicas.
2.  **Janela de Contexto (Top-K)**:
    *   Define quantos documentos o sistema lê antes de responder.
    *   *Default*: `5`. Aumentar melhora a fundamentação, mas deixa a resposta mais lenta.
3.  **System Prompt (Editável)**:
    *   O "Cérebro" (Fase 4) pode ser reescrito na interface.
    *   Permite ajustar o tom de voz ou adicionar novos axiomas de comportamento instantaneamente.
4.  **Limiar de Ambiguidade**:
    *   Define o quão "chato" o sistema é com perguntas vagas.
5.  **Variáveis de Ingestão**:
    *   Tamanho do Chunk, Sobreposição (Overlap) e estratégia de split.

---

## 3. Privacidade e Anonimização (PII Scrubber) 🕵️

O módulo `src.utils.privacy.PIIScrubber` atua como um "firewall de privacidade" bidirecional.

### Onde atua?
1.  **Na Entrada**: Antes da pergunta chegar ao LLM, CPFs e telefones são mascarados.
2.  **Na Saída (Audit Logs)**: Os logs salvam apenas a versão sanitizada. Mesmo se o banco vazar, a identidade dos cidadãos está protegida.

---

*Estado Atual: O Sentinela é um sistema governado, onde a qualidade do dado é validada por humanos e os parâmetros cognitivos são transparentes.*
