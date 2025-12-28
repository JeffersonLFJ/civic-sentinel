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

function startLogPolling(filterText = "") {
    miniLogContent.innerHTML = 'Conectando aos logs...';
    progressBar.style.width = '5%';
    progressText.innerText = '5%';

    // Clear previous logs to show only current operation
    miniLogContent.innerHTML = "";

    logInterval = setInterval(async () => {
        try {
            const res = await fetch('/api/admin/logs?lines=200');
            const data = await res.json();
            if (data.logs) {
                // Filter logs by filename (filterText)
                const filtered = filterText
                    ? data.logs.filter(line => line.includes(filterText) || line.includes("📊") || line.includes("🎉"))
                    : data.logs;

                miniLogContent.innerHTML = filtered.join('<br>');
                miniLogContent.scrollTop = miniLogContent.scrollHeight;

                const logsJoined = data.logs.join(' ');
                if (logsJoined.includes('🎉 Indexação concluída')) {
                    updateProgress(100);
                    showCloseButton();
                } else if (logsJoined.includes('📊 Progresso de indexação: Lote')) {
                    const match = logsJoined.match(/Lote (\d+)\/(\d+)/);
                    if (match) {
                        const current = parseInt(match[1]);
                        const total = parseInt(match[2]);
                        const prog = 80 + Math.floor((current / total) * 19);
                        updateProgress(prog);
                    } else {
                        updateProgress(85);
                    }
                } else if (logsJoined.includes('🧠 Iniciando indexação')) {
                    updateProgress(80);
                } else if (logsJoined.includes('🔍 Fragmentando texto')) {
                    updateProgress(75);
                } else if (logsJoined.includes('📝 Registro salvo')) {
                    updateProgress(70);
                } else if (logsJoined.includes('🗄️ Registrando metadados')) {
                    updateProgress(60);
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
    loadingSubtext.innerHTML = '<span style="color: #22c55e; font-weight: bold;">✅ Processamento concluído com sucesso!</span>';

    // Auto-close after 3 seconds
    setTimeout(() => {
        if (!loadingOverlay.classList.contains('hidden')) {
            hideLoading();
            fetchDocuments();
        }
    }, 3000);
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

// Scan Local logic
const scanLocalBtn = document.getElementById('scanLocalBtn');
const scanModal = document.getElementById('scanModal');
const scanTableBody = document.getElementById('scanTableBody');

scanLocalBtn.addEventListener('click', openScanModal);

function openScanModal() {
    scanModal.classList.remove('hidden');
    scanModal.style.display = 'flex';
    fetchLocalFiles();
}

function closeScanModal() {
    scanModal.classList.add('hidden');
    scanModal.style.display = 'none';
}

async function fetchLocalFiles() {
    scanTableBody.innerHTML = '<tr><td colspan="4">Buscando arquivos...</td></tr>';
    try {
        const res = await fetch('/api/admin/ingest/list');
        const data = await res.json();
        const files = data.files || [];

        if (files.length === 0) {
            scanTableBody.innerHTML = '<tr><td colspan="4">Nenhum arquivo encontrado em data/ingest.</td></tr>';
            return;
        }

        scanTableBody.innerHTML = files.map(f => `
            <tr>
                <td style="padding:10px;"><input type="checkbox" class="scan-checkbox" data-filename="${f.filename}"></td>
                <td style="padding:10px;">${f.filename}</td>
                <td style="padding:10px; color:#94a3b8;">${(f.size / 1024).toFixed(1)} KB</td>
                <td style="padding:10px;">
                    <select class="scan-type-select" style="background:#1e293b; border:1px solid #334155; color:white; padding:4px; border-radius:4px; font-size:0.85rem;">
                        <option value="lei" ${f.suggested_type === 'lei' ? 'selected' : ''}>Lei / Legislação (HTML)</option>
                        <option value="denuncia" ${f.suggested_type === 'denuncia' ? 'selected' : ''}>Documentos (Imagens e PDF)</option>
                        <option value="diario" ${f.suggested_type === 'diario' ? 'selected' : ''}>Diário Oficial</option>
                        <option value="tabela" ${f.suggested_type === 'tabela' ? 'selected' : ''}>Planilhas / Tabelas</option>
                    </select>
                </td>
            </tr>
        `).join('');
    } catch (e) {
        scanTableBody.innerHTML = `<tr><td colspan="4" style="color:red">Erro: ${e.message}</td></tr>`;
    }
}

window.toggleAllScan = (el) => {
    const checks = document.querySelectorAll('.scan-checkbox');
    checks.forEach(c => c.checked = el.checked);
};

window.applyBulkType = () => {
    const type = document.getElementById('bulkDocType').value;
    if (!type) return;
    const checks = document.querySelectorAll('.scan-checkbox:checked');
    checks.forEach(c => {
        const row = c.closest('tr');
        row.querySelector('.scan-type-select').value = type;
    });
};

window.processSelectedScan = async () => {
    const checks = document.querySelectorAll('.scan-checkbox:checked');
    if (checks.length === 0) return alert("Selecione ao menos um arquivo!");

    const items = Array.from(checks).map(c => ({
        filename: c.dataset.filename,
        doc_type: c.closest('tr').querySelector('.scan-type-select').value
    }));

    closeScanModal();
    showLoading("Processando Ingestão Local", `Iniciando processamento de ${items.length} arquivos...`);
    startLogPolling();

    try {
        const res = await fetch('/api/admin/ingest/process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ items })
        });
        const data = await res.json();
        // Progress will be updated by log polling
    } catch (e) {
        alert("Erro no processamento: " + e.message);
        hideLoading();
    }
};

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
    startLogPolling(file.name);

    const docType = document.getElementById('docType').value;

    const formData = new FormData();
    formData.append("file", file);
    formData.append("source", "admin");
    formData.append("doc_type", docType);

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
        if (docsTableBody) docsTableBody.innerHTML = '<tr><td colspan="6">Carregando...</td></tr>';

        // Parallel Fetch: Docs and Stats
        const [docsRes, statsRes] = await Promise.all([
            fetch(`${API_BASE}/?limit=50`),
            fetch('/api/admin/stats')
        ]);

        const docs = await docsRes.json();
        const stats = await statsRes.json();

        renderTable(docs);

        // Render Stats
        if (totalDocsEl) totalDocsEl.textContent = stats.total_documents;

    } catch (e) {
        console.error(e);
        if (docsTableBody) docsTableBody.innerHTML = '<tr><td colspan="6" style="color:red">Erro ao carregar dados.</td></tr>';
    }
}

function renderTable(docs) {
    if (!docsTableBody) return;
    docsTableBody.innerHTML = '';

    if (docs.length === 0) {
        docsTableBody.innerHTML = '<tr><td colspan="6">Nenhum documento encontrado.</td></tr>';
        return;
    }

    docs.forEach(doc => {
        const row = document.createElement('tr');

        const date = doc.publication_date || doc.created_at || '-';
        let source = 'Upload Manual';
        if (doc.source === 'api_querido_diario' || doc.source === 'official_gazette') source = 'Diário Oficial';
        if (doc.source === 'local_ingest') source = 'Vigilância Local';

        // Mapeamento amigável de tipos
        const typeMap = {
            'lei': '📜 Lei (HTML)',
            'denuncia': '📄 Documento (OCR)',
            'diario': '📰 Diário Oficial',
            'tabela': '📊 Planilha/Tabela'
        };
        const displayType = typeMap[doc.doc_type] || doc.doc_type || '-';

        // Status útil (Ref. Processamento)
        let statusDisplay = doc.ocr_method || 'Processado';
        if (statusDisplay === 'direct_pdf') statusDisplay = '📝 PDF Nativo';
        if (statusDisplay === 'tesseract') statusDisplay = '🔍 OCR (Tesseract)';
        if (statusDisplay === 'vision_fallback') statusDisplay = '👁️ IA Vision';
        if (statusDisplay === 'html_law_parser') statusDisplay = '🏛️ HTML Parser';

        row.innerHTML = `
            <td>${doc.filename}</td>
            <td><span style="font-size:0.8rem; padding:2px 6px; background:#334155; border-radius:4px;">${source}</span></td>
            <td><span style="font-size:0.8rem; color:#a5b4fc;">${displayType}</span></td>
            <td>${date}</td>
            <td><span style="font-size:0.85rem; color:#22c55e;">${statusDisplay}</span></td>
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
