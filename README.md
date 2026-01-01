# Sentinela Cívico 🛡️

**Sentinela Cívico** is an advanced retrieval-augmented generation (RAG) platform designed to monitor, ingest, and analyze civic documents (laws, decrees, official gazettes). It provides a semantic search interface and a cognitive agent to assist citizens and auditors in understanding public administration data.

## 🚀 Key Features

*   **Generative Chat**: Real-time Q&A with "Sentinela IA" using context from ingested documents.
*   **Audit Trail**: Full logging of interactions, sources used, and reasoning chains (CoT).
*   **Document Management**:
    *   **Dashboard**: Overview of indexed documents.
    *   **Upload**: Drag & drop support for PDF, TXT, HTML.
    *   **Local Scan**: Ingest massive datasets from the `data/ingest` folder.
*   **Staging Area (Quarentena)**: Human-in-the-loop validation for OCR text and metadata before indexing.
*   **Data Inspector**: Low-level visualization of vector chunks in ChromaDB.
*   **Cognitive Layout (Cérebro)**: Fine-tune LLM temperature, system prompts, and RAG retrieval parameters.

## 🏗 Architecture

*   **Backend**: Python, FastAPI, Uvicorn.
*   **Database**: SQLite (Metadata), ChromaDB (Vector Store).
*   **Frontend**: React 18, Vite, Tailwind CSS, React Router.
*   **AI Engine**: Ollama (LLM) + SentenceTransformers (Embeddings).

## 🛠️ Developer Guide

### Prerequisites
*   Python 3.9+
*   Node.js 18+
*   Docker (optional)

### Quick Start (Development Mode)

1.  **Start Backend**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    python3 -m uvicorn src.interfaces.api.main:app --host 0.0.0.0 --port 8000 --reload
    ```
    API available at: `http://localhost:8000/docs`

2.  **Start Frontend**
    ```bash
    cd src/interfaces/frontend
    npm install
    npm run dev
    ```
    UI available at: `http://localhost:5173/admin/`

### Production Build

The backend is configured to serve the frontend static files automatically.

1.  **Build Frontend**
    ```bash
    cd src/interfaces/frontend
    npm run build
    ```

2.  **Run Monolith**
    ```bash
    # From project root
    python3 -m uvicorn src.interfaces.api.main:app --host 0.0.0.0 --port 8000
    ```
    Access the full app at: `http://localhost:8000/admin/`

## 📁 Project Structure

```
├── data/                   # Persistent storage (SQLite, ChromaDB, Ingest)
├── docs/                   # Documentation
├── src/
│   ├── core/               # Database & Configuration
│   ├── domain/             # Business Logic (Ingestion, RAG)
│   ├── interfaces/
│   │   ├── api/            # FastAPI Routes
│   │   └── frontend/       # React Application
│   │       ├── src/
│   │       │   ├── components/ # Shared UI (Buttons, Layouts)
│   │       │   ├── features/   # Page Modules (Chat, Docs, Audit)
│   │       │   └── ...
│   └── utils/              # Helper functions
└── ...
```

## 📄 License
MPL 2.0
