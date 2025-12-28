const API_BASE = '/api/documents';
const UPLOAD_URL = '/api/upload/';

// Logs
const logsModal = document.getElementById('logsModal');
const logsContainer = document.getElementById('logsContainer');

function openLogs() {
    logsModal.classList.remove('hidden');
    logsModal.style.display = 'flex';
    fetchLogs();
}

function closeLogs() {
    logsModal.classList.add('hidden');
    logsModal.style.display = 'none';
}

async function fetchLogs() {
    logsContainer.innerHTML = 'Carregando...';
    try {
        const res = await fetch('/api/admin/logs?lines=200');
        const data = await res.json();

        if (data.logs && data.logs.length > 0) {
            logsContainer.innerHTML = data.logs.join('<br>');
            // Scroll to bottom
            logsContainer.scrollTop = logsContainer.scrollHeight;
        } else {
            logsContainer.innerHTML = '<i>Nenhum log encontrado ou arquivo vazio.</i>';
        }
    } catch (e) {
        logsContainer.innerHTML = `<span style="color:red">Erro ao carregar logs: ${e.message}</span>`;
    }
}

// Auditoria
const auditoriaModal = document.getElementById('auditoriaModal');
const auditTableBody = document.getElementById('auditTableBody');

function openAuditoriaModal() {
    auditoriaModal.classList.remove('hidden');
    auditoriaModal.style.display = 'flex';
    fetchAuditoria();
}

function closeAuditoria() {
    auditoriaModal.classList.add('hidden');
    auditoriaModal.style.display = 'none';
}

async function fetchAuditoria() {
    auditTableBody.innerHTML = '<tr><td colspan="4">Carregando auditoria...</td></tr>';
    try {
        const res = await fetch('/api/admin/stats');
        const data = await res.json();
        const logs = data.audit_logs || [];

        if (logs.length === 0) {
            auditTableBody.innerHTML = '<tr><td colspan="4">Nenhum log de auditoria encontrado.</td></tr>';
            return;
        }

        auditTableBody.innerHTML = logs.map(log => `
            <tr>
                <td style="padding:10px; border-bottom:1px solid #1e293b;">${new Date(log.timestamp).toLocaleString()}</td>
                <td style="padding:10px; border-bottom:1px solid #1e293b;"><span style="color:#a5b4fc">${log.action}</span></td>
                <td style="padding:10px; border-bottom:1px solid #1e293b; font-size:0.85rem">${log.details}</td>
                <td style="padding:10px; border-bottom:1px solid #1e293b; color:#22c55e">${log.confidence_score ? (log.confidence_score * 100).toFixed(0) + '%' : 'N/A'}</td>
            </tr>
        `).join('');
    } catch (e) {
        auditTableBody.innerHTML = `<tr><td colspan="4" style="color:red">Erro: ${e.message}</td></tr>`;
    }
}


// DOM Elements
const docsTableBody = document.getElementById('docsTableBody');
const totalDocsEl = document.getElementById('totalDocs');
const refreshBtn = document.getElementById('refreshBtn');
const uploadBtn = document.getElementById('uploadBtn'); // This element is still defined but its listener is replaced by 'openUploadBtn'
const uploadModal = document.getElementById('uploadModal');
const confirmUpload = document.getElementById('confirmUpload');
const cancelUpload = document.getElementById('cancelUpload');
const fileInput = document.getElementById('fileInput');

// Upload Logic
const loadingOverlay = document.getElementById('loadingOverlay');
const loadingText = document.getElementById('loadingText');
const loadingSubtext = document.getElementById('loadingSubtext');
const miniLogContent = document.getElementById('miniLogContent');
const progressBar = document.getElementById('progressBar');
const progressText = document.getElementById('progressText');
const closeLoadingBtn = document.getElementById('closeLoadingBtn');
let logInterval = null;

function startLogPolling() {
    miniLogContent.innerHTML = 'Conectando aos logs...';
    progressBar.style.width = '5%';
    progressText.innerText = '5%';

    logInterval = setInterval(async () => {
        try {
            const res = await fetch('/api/admin/logs?lines=50');
            const data = await res.json();
            if (data.logs) {
                miniLogContent.innerHTML = data.logs.join('<br>');
                miniLogContent.scrollTop = miniLogContent.scrollHeight;

                // Simple parser for progress based on keywords added in upload.py
                const logsJoined = data.logs.join(' ');
                if (logsJoined.includes('🎉 Indexação concluída')) {
                    updateProgress(100);
                    showCloseButton();
                } else if (logsJoined.includes('🧠 Gerando fragmentos')) {
                    updateProgress(80);
                } else if (logsJoined.includes('📝 Registro salvo')) {
                    updateProgress(60);
                } else if (logsJoined.includes('🗄️ Registrando metadados')) {
                    updateProgress(50);
                } else if (logsJoined.includes('✅ Texto extraído')) {
                    updateProgress(40);
                } else if (logsJoined.includes('🔍 Iniciando extração')) {
                    updateProgress(20);
                } else if (logsJoined.includes('💾 Salvando arquivo')) {
                    updateProgress(10);
                }
            }
        } catch (e) {
            console.error("Log poll failed", e);
        }
    }, 1500);
}

function updateProgress(val) {
    progressBar.style.width = `${val}%`;
    progressText.innerText = `${val}%`;
}

function showCloseButton() {
    stopLogPolling();
    closeLoadingBtn.style.display = 'block';
    loadingSubtext.innerText = "Processamento concluído com sucesso!";
}

function showLoading(title, sub) {
    loadingText.textContent = title;
    loadingSubtext.textContent = sub;
    loadingOverlay.classList.remove('hidden');
    loadingOverlay.style.display = 'flex';
    // Reset UI
    progressBar.style.width = '0%';
    progressText.innerText = '0%';
    closeLoadingBtn.style.display = 'none';
}

function hideLoading() {
    loadingOverlay.classList.add('hidden');
    loadingOverlay.style.display = 'none';
}

function stopLogPolling() {
    if (logInterval) clearInterval(logInterval);
    logInterval = null;
}

closeLoadingBtn.addEventListener('click', () => {
    hideLoading();
    fetchDocuments();
});

// Init
document.addEventListener('DOMContentLoaded', () => {
    fetchDocuments();
    if (localStorage.getItem('openLogs') === 'true') {
        localStorage.removeItem('openLogs');
        openLogs();
    }
});

// Actions
refreshBtn.addEventListener('click', fetchDocuments);

// Scan Local Action
const scanLocalBtn = document.getElementById('scanLocalBtn');
scanLocalBtn.addEventListener('click', async () => {
    showLoading("Escaneando Pasta Local", "Verificando data/ingest por novos documentos...");
    startLogPolling();
    try {
        const res = await fetch('/api/admin/ingest/local-scan', { method: 'POST' });
        const data = await res.json();
        alert(data.message);
        fetchDocuments();
    } catch (e) {
        alert("Erro no scan: " + e.message);
    } finally {
        if (!closeLoadingBtn.style.display || closeLoadingBtn.style.display === 'none') {
            hideLoading();
            stopLogPolling();
        }
    }
});

// Upload Action
uploadBtn.addEventListener('click', () => {
    document.getElementById('uploadModal').classList.remove('hidden');
    document.getElementById('uploadModal').style.display = 'flex';
});

document.getElementById('cancelUpload').addEventListener('click', () => {
    document.getElementById('uploadModal').classList.add('hidden');
    document.getElementById('uploadModal').style.display = 'none';
});

document.getElementById('confirmUpload').addEventListener('click', async () => {
    const file = fileInput.files[0];
    if (!file) return alert("Selecione um arquivo!");

    // Close modal, open overlay
    document.getElementById('uploadModal').classList.add('hidden');
    document.getElementById('uploadModal').style.display = 'none';

    showLoading("Enviando arquivo...", "O Sentinela está recebendo seu documento.");
    startLogPolling();

    const formData = new FormData();
    formData.append("file", file);
    formData.append("source", "admin");

    try {
        await fetch(UPLOAD_URL, {
            method: 'POST',
            body: formData
        });
        // fetchDocuments() is called by the manual close button now
    } catch (e) {
        hideLoading();
        stopLogPolling();
        alert(e.message);
    }
});

function closeModal() {
    uploadModal.classList.add('hidden');
    uploadModal.style.display = 'none';
}

// Logic
async function fetchDocuments() {
    try {
        docsTableBody.innerHTML = '<tr><td colspan="5">Carregando...</td></tr>';

        // Parallel Fetch: Docs and Stats
        const [docsRes, statsRes] = await Promise.all([
            fetch(`${API_BASE}/?limit=50`),
            fetch('/api/admin/stats')
        ]);

        const docs = await docsRes.json();
        const stats = await statsRes.json();

        renderTable(docs);

        // Render Stats
        totalDocsEl.textContent = stats.total_documents;

        // Update other cards if IDs existed (Added dynamically if needed or just logged)
        // I will assume simple update for now.

    } catch (e) {
        console.error(e);
        docsTableBody.innerHTML = '<tr><td colspan="5" style="color:red">Erro ao carregar dados.</td></tr>';
    }
}

function renderTable(docs) {
    docsTableBody.innerHTML = '';

    if (docs.length === 0) {
        docsTableBody.innerHTML = '<tr><td colspan="5">Nenhum documento encontrado.</td></tr>';
        return;
    }

    docs.forEach(doc => {
        const row = document.createElement('tr');

        const date = doc.publication_date || doc.created_at || '-';
        let source = 'Upload Manual';
        if (doc.source === 'api_querido_diario' || doc.source === 'official_gazette') source = 'Diário Oficial';
        if (doc.source === 'local_ingest') source = 'Vigilância Local';

        row.innerHTML = `
            <td>${doc.filename}</td>
            <td><span style="font-size:0.8rem; padding:2px 6px; background:#334155; border-radius:4px;">${source}</span></td>
            <td>${date}</td>
            <td>${doc.ocr_method || 'N/A'}</td>
            <td>
                <button class="btn danger-sm" onclick="requestDelete('${doc.id}')">Excluir</button>
            </td>
        `;
        docsTableBody.appendChild(row);
    });
}

// Delete Logic
let docToDelete = null;
const deleteModal = document.getElementById('deleteModal');

// Renamed from deleteDoc to avoid cached version issues
window.requestDelete = (id) => {
    console.log("Request delete for", id);
    docToDelete = id;
    deleteModal.classList.remove('hidden');
    deleteModal.style.display = 'flex';
};

document.getElementById('cancelDelete').addEventListener('click', () => {
    docToDelete = null;
    deleteModal.classList.add('hidden');
    deleteModal.style.display = 'none';
});

document.getElementById('confirmDelete').addEventListener('click', async () => {
    if (!docToDelete) return;

    const id = docToDelete;
    // Show loading state on button
    const btn = document.getElementById('confirmDelete');
    const originalText = btn.innerText;
    btn.innerText = "Excluindo...";
    btn.disabled = true;

    try {
        const res = await fetch(`${API_BASE}/${id}`, { method: 'DELETE' });
        if (res.ok) {
            deleteModal.classList.add('hidden');
            deleteModal.style.display = 'none';
            fetchDocuments();
        } else {
            alert("Erro ao excluir.");
        }
    } catch (e) {
        alert(e.message);
    } finally {
        btn.innerText = originalText;
        btn.disabled = false;
        docToDelete = null;
    }
});
