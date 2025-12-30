# Sentinela Cívico 🛡️

![Status](https://img.shields.io/badge/Status-Operacional-green) ![IA](https://img.shields.io/badge/IA-Local-blue) ![Versão](https://img.shields.io/badge/v-1.1-orange)

> **Vigilância Legislativa Soberana com Inteligência Artificial.**

O Sentinela Cívico é uma plataforma que "lê" o Diário Oficial, leis e decretos municipais, traduzindo o "juridiquês" para a linguagem do cidadão. Ele permite conversar com documentos oficiais, garantindo que a informação pública seja acessível, transparente e auditável.

---

## 🙋‍♀️ Para Leigos: Como Instalar e Usar

Este projeto foi desenhado para rodar no **seu computador**, garantindo que seus dados não saiam dali. Siga os passos abaixo (funciona em Mac, Linux e Windows com WSL).

### Passo 1: Instalar o "Cérebro" (Ollama)
O Sentinela usa um motor de Inteligência Artificial chamado Ollama.
1.  Acesse [ollama.ai](https://ollama.ai) e baixe o instalador para seu sistema.
2.  Instale e abra o programa.
3.  Abra seu Terminal (ou Prompt de Comando) e digite:
    ```bash
    ollama run gemma2:9b
    ```
    *Isso vai baixar os "pesos" da IA (aprox. 5GB). Espere terminar até aparecer um chat.*

### Passo 2: Baixar o Sentinela
Ainda no terminal, execute:
```bash
git clone https://github.com/JeffersonLFJ/civic-sentinel.git
cd civic-sentinel
```

### Passo 3: Preparar o Ambiente
Agora vamos instalar as ferramentas que o Sentinela usa (Python). Copie e cole linha por linha:

```bash
# 1. Cria um ambiente isolado (para não bagunçar seu sistema)
python3 -m venv venv

# 2. Ativa o ambiente
source venv/bin/activate  # (No Windows use: venv\Scripts\activate)

# 3. Instala os pacotes necessários
pip install -r requirements.txt
```

### Passo 4: Rodar o Sistema 🚀
Com tudo pronto, inicie o servidor:
```bash
python -m src.interfaces.api.main
```

Pronto! Abra seu navegador em: **`http://localhost:8000`**

---

## 🏛️ Contexto Social e Acadêmico

Este projeto integra a pesquisa de **Doutorado em Saúde Coletiva** de Jefferson Lopes, focada em **Justiça Epistêmica** e **Tecnologia Cívica** no território de **Tinguá (Nova Iguaçu/RJ)**.

### A Proposta: Inteligência Cívica
Em vez de usar IAs corporativas (como ChatGPT) que operam em "caixas pretas" na Califórnia, o Sentinela propõe uma **Soberania Digital Local**:
*   **Justiça Epistêmica**: O sistema é treinado para valorizar a realidade local. Ele prioriza decretos municipais e leis orgânicas sobre normas federais genéricas quando o assunto é o cotidiano da cidade.
*   **Transparência Radical**: Toda resposta da IA vem acompanhada de *citações clicáveis*. Se a IA não sabe, ela avisa; ela não inventa.
*   **Defesa de Direitos**: O "System Prompt" (personalidade da IA) é configurado para defender princípios constitucionais, servindo como um advogado de bolso para o cidadão comum.

### Responsabilidade com Dados
Diferente das grandes Big Techs, o Sentinela adota uma postura ética rigorosa:
1.  **Local-First**: Seus documentos (denúncias, diários) ficam no seu HD. Nada sobe para a nuvem.
2.  **Anonimização (PII Scrubbing)**: Um módulo de segurança remove automaticamente CPFs, telefones e nomes antes de processar qualquer texto.
3.  **Quarentena (Human-in-the-Loop)**: Nnhum documento entra no sistema sem aprovação humana. Isso evita a contaminação da base de conhecimento com "lixo" ou desinformação.

---

## 🧠 Arquitetura Técnica (Os 7 Pilares)

O sistema foi construído em fases modulares. Para detalhes técnicos profundos, consulte os relatórios de engenharia disponíveis na pasta de documentação:

1.  **[Ingestão e Fragmentação](docs/relatorio_fase_1_ingestao.md)**: Como transformamos PDFs e HTMLs em dados estruturados preservando a hierarquia legal.
2.  **[Base de Dados e Recuperação](docs/relatorio_fase_2_dados.md)**: A arquitetura híbrida (SQLite + ChromaDB) que permite a busca por conceitos e termos exatos.
3.  **[Raciocínio e Cognição](docs/relatorio_fase_3_raciocinio.md)**: O módulo de **Escuta Ativa** e **Intenção**, que extrai palavras-chave e pede clarificação antes de buscar.
4.  **[Engenharia de Prompt Jurídica](docs/relatorio_fase_4_juridico.md)**: A implementação da "Bússola Constitucional" e a Matriz de Decisão de Kelsen.
5.  **[Validação de Dados](docs/relatorio_fase_5_validacao.md)**: Os protocolos de Quarentena (`/admin/staging`) e o Firewall de Privacidade (PII Scrubber).
6.  **[Diagnósticos e Auditoria](docs/relatorio_fase_6_diagnosticos.md)**: A ferramenta "Raio-X" que explica o processo de pensamento da IA passo-a-passo.
7.  **Frontend (Em Breve)**: A interface visual que conectará o cidadão a essa inteligência.

**Infraestrutura**: Para detalhes sobre Stack, Versões e Segurança, veja o [Relatório de Infraestrutura](docs/security_and_infrastructure.md).

---

## ✨ "Vibe Coding" & Autoria

Este projeto explora uma nova fronteira de desenvolvimento de software: **Vibe Coding**.

*   **Direção Criativa & Ética**: Jefferson Lopes (Doutorando).
*   **Engenharia de Par**: Google Gemini 3 (High & Flash) via Google AntiGravity CLI.
*   **Metodologia**: Um fluxo de alta frequência onde a IA atua como arquiteta sênior e implementadora, guiada pelas regras de negócio e princípios éticos humanos.

---

## 📄 Licença

Código aberto sob licença **Mozilla Public License 2.0**.
*Desenvolvido em Tinguá para o Mundo.* 🌍🛡️
