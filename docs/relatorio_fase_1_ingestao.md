# Relatório Fase 1: Ingestão e Fragmentação (Sentinela) 📥

> **Foco**: Monitoramento Automático, OCR Multi-modal e Chunking Semântico.

Este relatório detalha a "Porta de Entrada" do sistema: como transformamos o caos de arquivos brutos em conhecimento estruturado para a Inteligência Artificial.

## 1. Mecanismo de Auto-Dispatch 🚦

O Sentinela implementa um roteador inteligente (`src/interfaces/api/routes/upload.py`) que decide a estratégia de processamento no momento em que o arquivo toca o disco, baseado no tipo de documento selecionado:

*   **Legislação (Leis/Decretos)**: Ativa o `Stateful Splitter` para preservar a hierarquia (Capítulo > Artigo > Inciso).
*   **Tabelas/Orçamentos**: Preserva a estrutura Markdown para que a IA consiga "cruzar" linhas e colunas sem perder a lógica.
*   **Diário Oficial**: Processamento em janelas deslizantes (`Sliding Window`) para garantir que o contexto não seja cortado no meio de um parágrafo.

---

## 2. Ingestão Híbrida (Vigilância 24/7)

O sistema opera em duas frentes:
1.  **Monitoramento Local (`LocalFolderIngestor`)**: Escaneia a pasta `data/ingest` em busca de novos arquivos (PDF, Imagens, TXT, HTML).
2.  **Conectividade Externa**: Integração com a API do *Querido Diário* para captura automática de gazetas municipais (Nova Iguaçu).

---

## 3. OCR Multi-modal e Visão Computacional 👁️

O Sentinela não se limita a ler textos; ele possui "capacidade visual" para tratar documentos de baixa qualidade ou fotos do mundo real.

### Fallback Inteligente
O motor de OCR (`OCREngine`) trabalha em cascata:
1.  **Tesseract (Fast Path)**: Executa o OCR tradicional em texto de boa qualidade.
2.  **Gemma Vision (Slow/Rich Path)**: Se a taxa de confiabilidade do Tesseract for baixa, o sistema aciona automaticamente o **Gemma3 (Visão)**. O modelo "olha" para o documento e realiza a transcrição semântica, corrigindo erros que o OCR comum cometeria.

### Parametrização pelo Admin
A taxa de confiabilidade para o gatilho de Visão é configurável em tempo real:
*   **Ajuste Fino**: No Painel de Admin (`Configurações`), o usuário pode definir o limiar (ex: 80%). Se o Tesseract retornar qualquer valor abaixo disso, a Visão do Gemma é invocada.
*   **Tratamento de PDF**: O sistema utiliza `pdf2image` para converter páginas complexas em imagens de alta densidade, garantindo a melhor entrada para os modelos de visão.

---

## 4. Fragmentação e Metadados (Contexto Rico)

Para que a IA não se perca, cada fragmento de texto ("chunk") é acompanhado de metadados:
*   **Sphere**: Federal, Estadual ou Municipal.
*   **DocType**: Lei, Decreto, Portaria, etc.
*   **Hierarchy**: Qual artigo ou página aquele trecho pertence.

**Resultado**: Quando o cidadão pergunta sobre um "Artigo 5º", o Sentinela sabe exatamente de *qual* lei o sistema está falando, impedindo alucinações de contexto cruzado.

---

*Estado Atual: O sistema é capaz de converter imagens borradas e documentos complexos em texto jurídico preciso e auditável.*
