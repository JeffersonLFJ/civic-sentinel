import React, { useState, useEffect } from 'react';
import { StatCard } from '../../components/ui/StatCard';
import { UploadModal } from './components/UploadModal';
import { ScanModal } from './components/ScanModal';
import { ConfirmationModal } from '../../components/ui/ConfirmationModal';

export const DocumentosPage = () => {
    const [docs, setDocs] = useState([]);
    const [stats, setStats] = useState({ total_documents: 0, last_ingestion: '-', sources: {} });
    const [loading, setLoading] = useState(true);

    // Modals
    const [isUploadOpen, setIsUploadOpen] = useState(false);
    const [isScanOpen, setIsScanOpen] = useState(false);

    const [deleteTarget, setDeleteTarget] = useState(null);
    const [selection, setSelection] = useState({});

    const fetchData = async () => {
        setLoading(true);
        try {
            // Parallel Fetch
            const [docsRes, statsRes] = await Promise.all([
                fetch('/api/documents/?limit=100').then(r => r.json()),
                fetch('/api/admin/stats').then(r => r.json())
            ]);

            // Handle Docs Response structure (can be array or {data: []})
            const docsData = Array.isArray(docsRes) ? docsRes : (docsRes.data || []);
            setDocs(docsData);
            setStats(statsRes);
            setSelection({}); // Reset selection on refresh
        } catch (error) {
            console.error("Failed to load Documents Dashboard", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const handleDelete = (id) => {
        setDeleteTarget([id]); // Handle as array for consistency
    };

    const handleBatchDelete = () => {
        const ids = docs.filter(d => selection[d.id]).map(d => d.id);
        if (ids.length > 0) {
            setDeleteTarget(ids);
        }
    };

    const toggleSelectAll = () => {
        const allSelected = docs.length > 0 && docs.every(d => selection[d.id]);
        const newSel = {};
        docs.forEach(d => newSel[d.id] = !allSelected);
        setSelection(newSel);
    };

    const confirmDelete = async () => {
        if (!deleteTarget || deleteTarget.length === 0) return;

        try {
            // Since we don't have a batch delete endpoint yet, we just loop delete calls
            // Ideally we should add DELETE /api/documents/batch but this is fine for < 50 docs
            await Promise.all(deleteTarget.map(id =>
                fetch(`/api/documents/${id}`, { method: 'DELETE' })
            ));

            fetchData(); // Refresh
            setDeleteTarget(null);
        } catch (e) {
            alert("Erro de conexão.");
        }
    };

    return (
        <div className="flex-1 flex flex-col bg-pattern h-full overflow-hidden">
            {/* Header / Stats */}
            <div className="flex-none px-10 py-8 border-b border-border bg-white/60 backdrop-blur-md z-10 sticky top-0 shadow-sm">
                <div className="flex items-start justify-between mb-8">
                    <div>
                        <h1 className="text-2xl font-bold text-text-main tracking-tight font-display mb-1">Gestão de Documentos</h1>
                        <p className="text-text-secondary text-sm font-medium">Administre a base de conhecimento do Sentinela.</p>
                    </div>
                    <div className="flex gap-3">
                        <button
                            onClick={() => setIsScanOpen(true)}
                            className="flex items-center gap-2 px-5 py-2 bg-white hover:bg-background-light text-text-secondary rounded-lg text-sm font-semibold transition-all border border-border shadow-sm group">
                            <span className="material-symbols-outlined text-[20px] group-hover:text-primary transition-colors">folder_open</span>
                            Scan Local
                        </button>
                        <button
                            onClick={() => setIsUploadOpen(true)}
                            className="flex items-center gap-2 px-5 py-2 bg-primary hover:bg-primary-hover text-white rounded-lg text-sm font-semibold transition-all shadow-lg shadow-primary/20 hover:shadow-primary/30 active:scale-95">
                            <span className="material-symbols-outlined text-[20px]">cloud_upload</span>
                            Novo Documento
                        </button>
                    </div>
                </div>

                <div className="flex flex-wrap gap-4">
                    <StatCard
                        icon="library_books"
                        label="Total Indexado"
                        value={stats.total_documents}
                        colorClass="bg-blue-50 text-accent-blue"
                    />
                    <StatCard
                        icon="history"
                        label="Última Ingestão"
                        value={(!stats.last_ingestion || stats.last_ingestion === "N/A" || stats.last_ingestion === "-") ? "N/A" : new Date(stats.last_ingestion).toLocaleDateString("pt-BR")}
                        colorClass="bg-emerald-50 text-emerald-600"
                    />
                    <StatCard
                        icon="warning"
                        label="Alertas de Risco"
                        value="0"
                        colorClass="bg-orange-50 text-orange-500"
                    />
                </div>
            </div>

            {/* List */}
            <div className="flex-1 overflow-y-auto p-10">
                <div className="bg-surface border border-border/60 rounded-2xl overflow-hidden shadow-card max-w-[1600px] mx-auto min-h-[500px] flex flex-col">
                    <div className="px-6 py-4 border-b border-border/40 bg-background-light flex justify-between items-center">
                        <div className="flex items-center gap-4">
                            <h3 className="font-bold text-text-main text-sm flex items-center gap-2">
                                <span className="material-symbols-outlined text-text-muted">list</span>
                                Base de Dados
                            </h3>
                            {/* Bulk Action */}
                            {Object.values(selection).filter(Boolean).length > 0 && (
                                <button
                                    onClick={handleBatchDelete}
                                    className="flex items-center gap-1.5 px-3 py-1 bg-red-50 text-red-600 border border-red-100 rounded-lg text-xs font-bold hover:bg-red-100 transition-colors animate-in fade-in slide-in-from-left-2">
                                    <span className="material-symbols-outlined text-[16px]">delete</span>
                                    Excluir Selecionados ({Object.values(selection).filter(Boolean).length})
                                </button>
                            )}
                        </div>

                        <div className="relative">
                            <span className="absolute inset-y-0 left-0 flex items-center pl-2 text-text-muted">
                                <span className="material-symbols-outlined text-[16px]">search</span>
                            </span>
                            <input className="bg-white border border-border rounded-lg pl-8 pr-3 py-1.5 text-xs w-64 focus:outline-none focus:ring-1 focus:ring-primary" placeholder="Filtrar arquivos..." />
                        </div>
                    </div>

                    <div className="flex-1 overflow-x-auto">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="border-b border-border/50 bg-background-light/50 text-xs font-bold text-text-secondary uppercase tracking-wider">
                                    <th className="px-6 py-4 w-10 text-center">
                                        <input
                                            type="checkbox"
                                            checked={docs.length > 0 && docs.every(d => selection[d.id])}
                                            onChange={toggleSelectAll}
                                            className="rounded border-border text-primary focus:ring-primary/20 cursor-pointer size-4"
                                        />
                                    </th>
                                    <th className="px-6 py-4">Arquivo / ID</th>
                                    <th className="px-6 py-4">Contexto</th>
                                    <th className="px-6 py-4">Data Ingestão</th>
                                    <th className="px-6 py-4">Status</th>
                                    <th className="px-6 py-4 text-right">Ações</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-border/40">
                                {loading ? (
                                    <tr><td colSpan="6" className="p-10 text-center text-text-muted">Carregando base de conhecimento...</td></tr>
                                ) : docs.length === 0 ? (
                                    <tr><td colSpan="6" className="p-10 text-center text-text-muted">Nenhum documento encontrado.</td></tr>
                                ) : (
                                    docs.map(doc => (
                                        <tr key={doc.id} className={`hover:bg-background-light/50 transition-colors group ${selection[doc.id] ? 'bg-primary/5' : ''}`}>
                                            <td className="px-6 py-4 text-center">
                                                <input
                                                    type="checkbox"
                                                    checked={!!selection[doc.id]}
                                                    onChange={() => setSelection(prev => ({ ...prev, [doc.id]: !prev[doc.id] }))}
                                                    className="rounded border-border text-primary focus:ring-primary/20 cursor-pointer size-4"
                                                />
                                            </td>
                                            <td className="px-6 py-4">
                                                <div className="flex items-center gap-3">
                                                    <div className="size-8 rounded bg-primary-soft/50 text-primary flex items-center justify-center border border-primary/10">
                                                        <span className="material-symbols-outlined text-[18px]">description</span>
                                                    </div>
                                                    <div>
                                                        <p className="text-sm font-semibold text-text-main line-clamp-1 max-w-[300px]" title={doc.filename}>{doc.filename}</p>
                                                        <p className="text-[10px] text-text-muted font-mono">{doc.id.substring(0, 8)}...</p>
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4">
                                                <div className="flex flex-col gap-1 items-start">
                                                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-gray-100 text-gray-600 border border-gray-200">
                                                        {doc.source || 'Upload'}
                                                    </span>
                                                    {doc.sphere && (
                                                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-blue-50 text-blue-600 border border-blue-100 uppercase">
                                                            {doc.sphere}
                                                        </span>
                                                    )}
                                                </div>
                                            </td>
                                            <td className="px-6 py-4 text-sm text-text-secondary">
                                                {new Date(doc.created_at).toLocaleString()}
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wide border ${doc.status === 'active' ? 'bg-emerald-50 text-emerald-600 border-emerald-100' : 'bg-yellow-50 text-yellow-600 border-yellow-100'
                                                    }`}>
                                                    <span className={`size-1.5 rounded-full ${doc.status === 'active' ? 'bg-emerald-500' : 'bg-yellow-500'}`}></span>
                                                    {doc.status || 'Pendente'}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 text-right">
                                                <button
                                                    onClick={() => handleDelete(doc.id)}
                                                    className="p-1.5 rounded text-text-muted hover:text-red-500 hover:bg-red-50 transition-colors" title="Excluir">
                                                    <span className="material-symbols-outlined text-[20px]">delete</span>
                                                </button>
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            {/* Modals */}
            <UploadModal isOpen={isUploadOpen} onClose={() => setIsUploadOpen(false)} onSuccess={fetchData} />
            <ScanModal isOpen={isScanOpen} onClose={() => setIsScanOpen(false)} onSuccess={fetchData} />
            <ConfirmationModal
                isOpen={!!deleteTarget}
                onClose={() => setDeleteTarget(null)}
                onConfirm={confirmDelete}
                title={deleteTarget?.length > 1 ? `Excluir ${deleteTarget.length} Documentos` : "Excluir Documento"}
                message={deleteTarget?.length > 1 ?
                    "Tem certeza que deseja excluir permanentemente estes documentos selecionados?" :
                    "Tem certeza que deseja excluir permanentemente este documento? Esta ação não pode ser desfeita."
                }
                confirmText={deleteTarget?.length > 1 ? "Excluir Todos" : "Excluir Definitivamente"}
                isDangerous={true}
            />

        </div>
    );
};

export default DocumentosPage;
