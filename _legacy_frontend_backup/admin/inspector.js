const API_DOCS = '/api/documents';
const API_INSPECT = '/api/admin/inspect';

const docList = document.getElementById('docList');
const chunkViewer = document.getElementById('chunkViewer');

async function init() {
    try {
        const res = await fetch(`${API_DOCS}/?limit=50`);
        const docs = await res.json();
        renderDocList(docs);
    } catch (e) {
        docList.innerHTML = `<span style="color:red">Erro: ${e.message}</span>`;
    }
}

function renderDocList(docs) {
    docList.innerHTML = '';
    docs.forEach(doc => {
        const div = document.createElement('div');
        div.className = 'doc-item';
        div.innerHTML = `
            <div style="font-weight:600">${doc.filename}</div>
            <div style="font-size:0.8rem; color:#94a3b8">${doc.id.substring(0, 8)}...</div>
        `;
        div.onclick = () => {
            document.querySelectorAll('.doc-item').forEach(el => el.classList.remove('active'));
            div.classList.add('active');
            loadChunks(doc.id, doc.filename);
        };
        docList.appendChild(div);
    });
}

async function loadChunks(docId, filename) {
    chunkViewer.innerHTML = '<p style="color:#94a3b8">Carregando chunks...</p>';

    try {
        const res = await fetch(`${API_INSPECT}/${docId}`);
        const data = await res.json();

        if (data.error) {
            chunkViewer.innerHTML = `<p style="color:red">Erro: ${data.error}</p>`;
            return;
        }

        renderChunks(data, filename);
    } catch (e) {
        chunkViewer.innerHTML = `<p style="color:red">Erro de conexão: ${e.message}</p>`;
    }
}

function renderChunks(data, filename) {
    const chunks = data.chunks || [];
    const count = data.total_chunks || 0;

    let html = `
        <div style="margin-bottom: 20px; border-bottom: 1px solid #334155; padding-bottom: 10px;">
            <h3>${filename}</h3>
            <span style="color: #94a3b8">Total de Chunks Indexados: <strong>${count}</strong></span>
        </div>
    `;

    if (count === 0) {
        html += '<p>Nenhum texto encontrado para este documento.</p>';
        chunkViewer.innerHTML = html;
        return;
    }

    chunks.forEach((chunk, index) => {
        html += `
            <div class="chunk-card">
                <div class="chunk-meta">
                    <span>Chunk #${index + 1}</span>
                    <span>chars: ${chunk.full_length}</span>
                </div>
                <div class="chunk-text">${escapeHtml(chunk.content)}</div>
            </div>
        `;
    });

    chunkViewer.innerHTML = html;
}

function escapeHtml(text) {
    if (!text) return '';
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

document.addEventListener('DOMContentLoaded', init);
