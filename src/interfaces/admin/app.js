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

// Navegação entre Seções (Página Inteira)
function showSection(section) {
    document.getElementById('docsSection').classList.add('hidden');
    document.getElementById('auditSection').classList.add('hidden');
    document.getElementById('stagingSection').classList.add('hidden');

    document.getElementById('docsNav').classList.remove('active');
    document.getElementById('auditNav').classList.remove('active');
    document.getElementById('stagingNav').classList.remove('active');

    if (section === 'docs') {
        document.getElementById('docsSection').classList.remove('hidden');
        document.getElementById('docsNav').classList.add('active');
        fetchDocuments();
    } else if (section === 'audit') {
        document.getElementById('auditSection').classList.remove('hidden');
        document.getElementById('auditNav').classList.add('active');
        fetchAuditoria();
    } else if (section === 'staging') {
        document.getElementById('stagingSection').classList.remove('hidden');
        document.getElementById('stagingNav').classList.add('active');
        fetchStaging();
    }
}
window.showSection = showSection;

// Auditoria
const auditTableBody = document.getElementById('auditTableBody');

async function clearAuditLogs() {
    const confirmed = await showConfirm("Tem certeza que deseja apagar TODO o histórico de auditoria?", "Limpar Auditoria", "Apagar Tudo");
    if (!confirmed) return;

    try {
        const res = await fetch('/api/admin/audit', { method: 'DELETE' });
        const data = await res.json();
        if (res.ok) {
            toast.success(data.message);
            fetchAuditoria();
        } else {
            toast.error("Erro: " + data.detail);
        }
    } catch (e) {
        toast.error("Erro de conexão: " + e.message);
    }
}

async function fetchAuditoria() {
    auditTableBody.innerHTML = '<tr><td colspan="3">Carregando auditoria...</td></tr>';
    try {
        const res = await fetch('/api/admin/stats');
        const data = await res.json();
        const logs = data.audit_logs || [];

        if (logs.length === 0) {
            auditTableBody.innerHTML = '<tr><td colspan="3">Nenhum log de auditoria encontrado.</td></tr>';
            return;
        }

        auditTableBody.innerHTML = logs.map(log => {
            const date = new Date(log.timestamp).toLocaleString();
            const queryPreview = log.query ? log.query.substring(0, 60) + "..." : "<i>Ação: " + log.action + "</i>";

            let badgeClass = 'badge-low';
            if (log.confidence_score >= 0.7) badgeClass = 'badge-high';
            else if (log.confidence_score >= 0.4) badgeClass = 'badge-mid';

            return `
                <tr onclick="openInspector('${log.id}')">
                    <td style="padding:10px; border-bottom:1px solid #1e293b; font-size:0.8rem;">${date}</td>
                    <td style="padding:10px; border-bottom:1px solid #1e293b;">${queryPreview}</td>
                    <td style="padding:10px; border-bottom:1px solid #1e293b;">
                        <span class="confidence-badge ${badgeClass}">${(log.confidence_score * 100).toFixed(0)}%</span>
                    </td>
                </tr>
            `;
        }).join('');
    } catch (e) {
        auditTableBody.innerHTML = `<tr><td colspan="3" style="color:red">Erro: ${e.message}</td></tr>`;
    }
}

async function openInspector(logId) {
    const inspectorContent = document.getElementById('inspectorContent');
    inspectorContent.innerHTML = '<div style="text-align:center; padding:40px;"><div class="spinner"></div><p>Analisando rastros...</p></div>';

    try {
        const res = await fetch(`/api/admin/audit/${logId}`);
        const log = await res.json();

        // Parse sources if present
        let sourcesHtml = '<p style="color:#94a3b8;">Nenhuma fonte documental citada.</p>';
        if (log.sources_json) {
            const sources = JSON.parse(log.sources_json);
            sourcesHtml = sources.map((s, idx) => `
                <div class="chunk-card">
                    <div style="font-weight:600; color:#3b82f6; margin-bottom:5px; font-size:0.75rem;">
                        FRAGMENTO ${idx + 1}: ${s.filename} (${s.source})
                    </div>
                    ${s.content}
                </div>
            `).join('');
        }

        inspectorContent.innerHTML = `
            <div class="inspector-card">
                <h5>Pergunta do Usuário</h5>
                <p style="font-size:1.1rem; font-weight:600;">"${log.query || '(sem pergunta)'}"</p>
            </div>

            <div class="inspector-card" style="border-left: 4px solid #22c55e;">
                <h5>Resposta do Sentinela</h5>
                <p style="white-space: pre-wrap;">${log.response || '(sem resposta)'}</p>
            </div>

            <div class="inspector-card">
                <h5>Base de Conhecimento RAG (Citações)</h5>
                ${sourcesHtml}
            </div>

            <div class="inspector-card" style="font-size:0.8rem; color:#94a3b8;">
                <p>ID da Operação: ${log.id}</p>
                <p>Ação: ${log.action}</p>
                <p>Confiança Bruta: ${log.confidence_score}</p>
            </div>
        `;
    } catch (e) {
        inspectorContent.innerHTML = `<div style="color:red; padding:20px;">Erro ao carregar detalhes: ${e.message}</div>`;
    }
}
window.openInspector = openInspector;
window.fetchAuditoria = fetchAuditoria;
window.clearAuditLogs = clearAuditLogs;


// Prompt Editor Logic
const promptBtn = document.getElementById('promptBtn');
const promptModal = document.getElementById('promptModal');
const systemPromptInput = document.getElementById('systemPromptInput');

promptBtn.addEventListener('click', openPromptModal);

async function openPromptModal() {
    promptModal.classList.remove('hidden');
    promptModal.style.display = 'flex';
    systemPromptInput.value = "Carregando...";
    try {
        const res = await fetch('/api/admin/prompt');
        const data = await res.json();
        systemPromptInput.value = data.content;
    } catch (e) {
        systemPromptInput.value = "Erro ao carregar prompt: " + e.message;
    }
}

function closePromptModal() {
    promptModal.classList.add('hidden');
    promptModal.style.display = 'none';
}

// --- Quarentena (Staging Area) ---

async function fetchStaging() {
    const tableBody = document.getElementById('stagingTableBody');
    tableBody.innerHTML = '<tr><td colspan="5">Carregando quarentena...</td></tr>';

    try {
        const response = await fetch('/api/admin/staging');
        const data = await response.json();

        if (data.status === 'success') {
            tableBody.innerHTML = '';
            if (data.documents.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="5">Vazio. Nenhuma pendência na quarentena.</td></tr>';
            }
            data.documents.forEach(doc => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td><a href="#" onclick="inspectDocumentStaging('${doc.id}', '${doc.filename}')" style="color: #3b82f6; text-decoration: underline;">${doc.filename}</a></td>
                    <td>
                        <select id="type_${doc.id}" class="staging-select">
                            <option value="lei_ordinaria" ${doc.doc_type === 'lei_ordinaria' ? 'selected' : ''}>Lei Ordinária</option>
                            <option value="constituicao" ${doc.doc_type === 'constituicao' ? 'selected' : ''}>Constituição</option>
                            <option value="decreto" ${doc.doc_type === 'decreto' ? 'selected' : ''}>Decreto</option>
                            <option value="portaria" ${doc.doc_type === 'portaria' ? 'selected' : ''}>Portaria</option>
                            <option value="diario_oficial" ${doc.doc_type === 'diario_oficial' ? 'selected' : ''}>Diário Oficial</option>
                            <option value="documento_geral" ${doc.doc_type === 'documento_geral' ? 'selected' : ''}>Geral</option>
                        </select>
                    </td>
                    <td>
                        <select id="sphere_${doc.id}" class="staging-select">
                            <option value="municipal" ${doc.sphere === 'municipal' ? 'selected' : ''}>Municipal</option>
                            <option value="federal" ${doc.sphere === 'federal' ? 'selected' : ''}>Federal</option>
                            <option value="estadual" ${doc.sphere === 'estadual' ? 'selected' : ''}>Estadual</option>
                            <option value="unknown" ${doc.sphere === 'unknown' ? 'selected' : ''}>Desconhecida</option>
                        </select>
                    </td>
                    <td><input type="date" id="date_${doc.id}" value="${doc.publication_date || ''}" class="staging-input"></td>
                    <td>
                        <button onclick="approveStaging('${doc.id}')" class="btn primary-sm">Aprovar</button>
                        <button onclick="deleteDoc('${doc.id}')" class="btn danger-sm" style="margin-left: 5px;">Excluir</button>
                    </td>
                `;
                tableBody.appendChild(row);
            });
        }
    } catch (e) {
        tableBody.innerHTML = `<tr><td colspan="5">Erro ao carregar: ${e.message}</td></tr>`;
    }
}

async function inspectDocumentStaging(id, filename) {
    document.getElementById('inspectTitle').innerText = `Inspecionando: ${filename}`;
    document.getElementById('inspectTextBody').innerText = "Carregando texto...";
    document.getElementById('inspectModal').classList.remove('hidden');

    try {
        const response = await fetch(`/api/admin/staging/${id}/text`);
        const data = await response.json();
        document.getElementById('inspectTextBody').innerText = data.text;
    } catch (e) {
        document.getElementById('inspectTextBody').innerText = "Erro ao carregar texto.";
    }
}

function closeInspectModal() {
    document.getElementById('inspectModal').classList.add('hidden');
}

async function approveStaging(id) {
    const type = document.getElementById(`type_${id}`).value;
    const sphere = document.getElementById(`sphere_${id}`).value;
    const date = document.getElementById(`date_${id}`).value;

    try {
        const response = await fetch(`/api/admin/staging/${id}/approve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ doc_type: type, sphere: sphere, publication_date: date })
        });
        const result = await response.json();
        if (result.status === 'success') {
            toast.success("Documento aprovado e indexado!");
            fetchStaging();
            fetchDocuments();
        } else {
            toast.error("Erro: " + result.detail);
        }
    } catch (e) {
        toast.error("Erro na aprovação: " + e.message);
    }
}

async function approveAllStaging() {
    const stagingTable = document.getElementById('stagingTableBody');
    const rows = stagingTable.querySelectorAll('tr');
    if (rows.length === 0 || rows[0].innerText.includes("Vazio")) {
        toast.warning("Nada para aprovar.");
        return;
    }

    const confirmed = await showConfirm("Isso aprovará TODOS os documentos com os metadados atuais. Continuar?", "Aprovar Tudo", "Aprovar Todos", "primary");
    if (!confirmed) return;

    for (const row of rows) {
        const btn = row.querySelector('button.primary-sm');
        if (btn) {
            btn.click();
            await new Promise(r => setTimeout(r, 1000));
        }
    }
}

async function saveSystemPrompt() {
    const newContent = systemPromptInput.value;
    try {
        const res = await fetch('/api/admin/prompt', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: newContent })
        });
        if (res.ok) {
            toast.success("Prompt salvo com sucesso!");
            closePromptModal();
        } else {
            toast.error("Erro ao salvar prompt.");
        }
    } catch (e) {
        toast.error("Erro de conexão: " + e.message);
    }
}
window.closePromptModal = closePromptModal; // Make global for onclick
window.saveSystemPrompt = saveSystemPrompt;

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
                        <option value="lei_ordinaria" ${f.suggested_type === 'lei_ordinaria' ? 'selected' : ''}>📜 Lei Ordinária</option>
                        <option value="lei_complementar" ${f.suggested_type === 'lei_complementar' ? 'selected' : ''}>📜 Lei Complementar</option>
                        <option value="constituicao" ${f.suggested_type === 'constituicao' ? 'selected' : ''}>⚖️ Constituição</option>
                        <option value="decreto" ${f.suggested_type === 'decreto' ? 'selected' : ''}>📄 Decreto</option>
                        <option value="portaria" ${f.suggested_type === 'portaria' ? 'selected' : ''}>📄 Portaria</option>
                        <option value="diario_oficial" ${f.suggested_type === 'diario_oficial' ? 'selected' : ''}>📰 Diário Oficial</option>
                        <option value="tabela" ${f.suggested_type === 'tabela' ? 'selected' : ''}>📊 Planilha / Tabela</option>
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
    if (checks.length === 0) {
        toast.warning("Selecione ao menos um arquivo!");
        return;
    }

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
        toast.error("Erro no processamento: " + e.message);
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
    if (!file) {
        toast.warning("Selecione um arquivo!");
        return;
    }

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
        toast.error(e.message);
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

        const date = doc.publication_date || (doc.created_at ? doc.created_at.split('T')[0] : '-');
        let source = 'Upload Manual';
        if (doc.source === 'api_querido_diario' || doc.source === 'official_gazette') source = 'Diário Oficial';
        if (doc.source === 'local_ingest') source = 'Vigilância Local';

        const typeMap = {
            'lei_ordinaria': '📜 Lei Ordinária',
            'lei_complementar': '📜 Lei Complementar',
            'constituicao': '⚖️ Constituição',
            'decreto': '📄 Decreto',
            'portaria': '📄 Portaria',
            'diario_oficial': '📰 Diário Oficial',
            'tabela': '📊 Planilha / Tabela'
        };
        const displayType = typeMap[doc.doc_type] || doc.doc_type || '-';
        const displaySphere = doc.sphere ? doc.sphere.toUpperCase() : '-';

        // Status visual
        let statusBadge = `<span class="badge ${doc.status === 'active' ? 'badge-high' : 'badge-low'}">
            ${doc.status === 'active' ? 'Ativo' : 'Pendente'}
        </span>`;

        row.innerHTML = `
            <td>${doc.filename}</td>
            <td><span style="font-size:0.8rem; padding:2px 6px; background:#334155; border-radius:4px;">${source}</span></td>
            <td><span style="font-size:0.8rem; color:#a5b4fc;">${displayType}</span></td>
            <td><span style="font-size:0.8rem;">${displaySphere}</span></td>
            <td>${date}</td>
            <td>${statusBadge}</td>
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
            toast.error("Erro ao excluir.");
        }
    } catch (e) {
        toast.error(e.message);
    } finally {
        btn.innerText = originalText;
        btn.disabled = false;
        docToDelete = null;
    }
});
