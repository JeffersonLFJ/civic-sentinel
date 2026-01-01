import React, { useState, useEffect } from 'react';
import { ReviewModal } from './components/ReviewModal';

export const StagingPage = () => {
    const [pendingDocs, setPendingDocs] = useState([]);
    const [queuedDocs, setQueuedDocs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [processingBatch, setProcessingBatch] = useState(false);
    const [selectedDoc, setSelectedDoc] = useState(null); // {id, filename}

    const [progress, setProgress] = useState({ processed: 0, total: 0, errors: 0, current: '' });

    const fetchData = async () => {
        setLoading(true);
        try {
            // Fetch Pending
            const resPending = await fetch('/api/admin/staging');
            const dataPending = await resPending.json();
            setPendingDocs(dataPending.documents || []);

            // Fetch Queued
            const resQueued = await fetch('/api/admin/staging/queued');
            const dataQueued = await resQueued.json();
            setQueuedDocs(dataQueued.documents || []);
        } catch (error) {
            console.error("Failed to fetch staging data", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const handleSuccess = () => {
        setSelectedDoc(null);
        fetchData(); // Refresh lists
    };

    const handleProcessBatch = async () => {
        if (queuedDocs.length === 0) return;
        setProcessingBatch(true);
        setProgress({ processed: 0, total: queuedDocs.length, errors: 0, current: 'Iniciando...' });

        const errors = [];

        try {
            for (let i = 0; i < queuedDocs.length; i++) {
                const doc = queuedDocs[i];
                setProgress(prev => ({ ...prev, current: `Indexando ${doc.filename}...` }));

                try {
                    const res = await fetch(`/api/admin/staging/${doc.id}/activate`, { method: 'POST' });
                    if (!res.ok) {
                        const data = await res.json();
                        throw new Error(data.detail || 'Failed');
                    }
                    setProgress(prev => ({ ...prev, processed: prev.processed + 1 }));
                } catch (e) {
                    console.error(e);
                    errors.push(`${doc.filename}: ${e.message}`);
                    setProgress(prev => ({ ...prev, errors: prev.errors + 1 }));
                }
            }

            alert(`Processamento concluído!\n\n${queuedDocs.length - errors.length} processados.\n${errors.length} erros.`);
            fetchData();
        } catch (e) {
            alert("Erro fatal no processamento.");
        } finally {
            setProcessingBatch(false);
            setProgress({ processed: 0, total: 0, errors: 0, current: '' });
        }
    };

    return (
        <div className="flex-1 flex flex-col bg-pattern h-full overflow-hidden relative">
            {/* Progress Overlay */}
            {processingBatch && (
                <div className="absolute inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
                    <div className="bg-surface border border-border rounded-2xl shadow-2xl w-full max-w-md p-6 animate-in zoom-in-95">
                        <h3 className="text-lg font-bold text-text-main mb-4 flex items-center gap-2">
                            <span className="size-5 border-2 border-primary/30 border-t-primary rounded-full animate-spin"></span>
                            Processando Fila...
                        </h3>
                        <div className="w-full bg-background-light rounded-full h-2.5 mb-2 overflow-hidden">
                            <div
                                className="bg-primary h-2.5 rounded-full transition-all duration-300 ease-out"
                                style={{ width: `${(progress.processed + progress.errors) / progress.total * 100}%` }}
                            ></div>
                        </div>
                        <div className="flex justify-between text-xs text-text-muted mb-4">
                            <span>{progress.processed + progress.errors} de {progress.total} documentos</span>
                            <span>{Math.round(((progress.processed + progress.errors) / progress.total) * 100)}%</span>
                        </div>
                        <p className="text-sm text-text-secondary truncate font-mono bg-background p-2 rounded border border-border/50">
                            {progress.current}
                        </p>
                        {progress.errors > 0 && (
                            <p className="text-xs text-red-500 mt-2">Erros encontrados: {progress.errors}</p>
                        )}
                    </div>
                </div>
            )}

            {/* Header */}
            <div className="flex-none px-10 py-8 border-b border-border bg-white/60 backdrop-blur-md z-10 sticky top-0 shadow-sm">
                <div className="flex items-start justify-between">
                    <div>
                        <h1 className="text-2xl font-bold text-text-main tracking-tight font-display mb-1">Quarentena & Processamento</h1>
                        <p className="text-text-secondary text-sm font-medium">Revise documentos pendentes e monitore a fila de ingestão.</p>
                    </div>
                    <div className="flex gap-3">
                        <button
                            onClick={fetchData}
                            className="flex items-center gap-2 px-4 py-2 bg-white hover:bg-background-light text-text-secondary rounded-lg text-sm font-semibold transition-all border border-border shadow-sm group">
                            <span className="material-symbols-outlined group-hover:rotate-180 transition-transform">refresh</span>
                            Atualizar
                        </button>
                        {queuedDocs.length > 0 && (
                            <button
                                onClick={handleProcessBatch}
                                disabled={processingBatch}
                                className="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-lg text-sm font-semibold transition-all shadow-lg shadow-primary/20 disabled:opacity-50 disabled:cursor-not-allowed animate-in fade-in slide-in-from-right-4"
                            >
                                <span className="material-symbols-outlined">play_arrow</span>
                                Processar Fila ({queuedDocs.length})
                            </button>
                        )}
                    </div>
                </div>

                <div className="flex gap-4 mt-6">
                    {/* Stat Cards */}
                    <div className="bg-orange-50 border border-orange-100 rounded-lg p-3 px-4 flex items-center gap-3">
                        <span className="material-symbols-outlined text-orange-500">pending_actions</span>
                        <div>
                            <p className="text-xs font-bold text-orange-800 uppercase tracking-wider">Pendentes de Revisão</p>
                            <p className="text-xl font-black text-orange-900 leading-none mt-0.5">{pendingDocs.length}</p>
                        </div>
                    </div>
                    <div className="bg-blue-50 border border-blue-100 rounded-lg p-3 px-4 flex items-center gap-3">
                        <span className="material-symbols-outlined text-blue-500">layers</span>
                        <div>
                            <p className="text-xs font-bold text-blue-800 uppercase tracking-wider">Na Fila de Processamento</p>
                            <p className="text-xl font-black text-blue-900 leading-none mt-0.5">{queuedDocs.length}</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Content Lists */}
            <div className="flex-1 overflow-y-auto p-10 space-y-8">

                {/* 1. Pending List */}
                <div className="space-y-4">
                    <h3 className="text-lg font-bold text-text-main flex items-center gap-2">
                        <span className="material-symbols-outlined text-orange-500">pending</span>
                        Aguardando Revisão Manual
                    </h3>
                    <div className="bg-surface border border-border/60 rounded-2xl overflow-hidden shadow-card">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="border-b border-border/50 bg-background-light/50 text-xs font-bold text-text-secondary uppercase tracking-wider">
                                    <th className="px-6 py-4">Documento</th>
                                    <th className="px-6 py-4">Tags</th>
                                    <th className="px-6 py-4">Data Upload</th>
                                    <th className="px-6 py-4 text-right">Ação</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-border/40">
                                {loading ? (
                                    <tr><td colSpan="4" className="p-10 text-center text-text-muted">Carregando...</td></tr>
                                ) : pendingDocs.length === 0 ? (
                                    <tr><td colSpan="4" className="p-10 text-center text-text-muted italic">Nenhum documento pendente.</td></tr>
                                ) : (
                                    pendingDocs.map(doc => (
                                        <tr key={doc.id} className="hover:bg-background-light/50 transition-colors">
                                            <td className="px-6 py-4">
                                                <div className="flex items-center gap-3">
                                                    <div className="size-8 rounded bg-background border border-border flex items-center justify-center text-text-muted">
                                                        <span className="material-symbols-outlined text-[18px]">description</span>
                                                    </div>
                                                    <div>
                                                        <p className="text-sm font-semibold text-text-main line-clamp-1 max-w-[300px]" title={doc.filename}>{doc.filename}</p>
                                                        <p className="text-[10px] text-text-muted font-mono">{doc.id.slice(0, 8)}...</p>
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4">
                                                {doc.custom_tags ? (
                                                    <div className="flex gap-1 flex-wrap">
                                                        {doc.custom_tags.split(',').map((tag, i) => (
                                                            <span key={i} className="px-1.5 py-0.5 bg-background-light border border-border rounded text-[10px] text-text-secondary">{tag.trim()}</span>
                                                        ))}
                                                    </div>
                                                ) : <span className="text-text-muted text-xs">-</span>}
                                            </td>
                                            <td className="px-6 py-4 text-xs text-text-secondary">
                                                {new Date(doc.created_at).toLocaleDateString()}
                                            </td>
                                            <td className="px-6 py-4 text-right">
                                                <button
                                                    onClick={() => setSelectedDoc(doc)}
                                                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white border border-border hover:border-primary hover:text-primary transition-all text-xs font-medium shadow-sm"
                                                >
                                                    Revisar
                                                </button>
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* 2. Queued List */}
                {queuedDocs.length > 0 && (
                    <div className="space-y-4 opacity-80 hover:opacity-100 transition-opacity">
                        <h3 className="text-lg font-bold text-text-main flex items-center gap-2">
                            <span className="material-symbols-outlined text-blue-500">hourglass_top</span>
                            Fila de Processamento (Próximo Batch)
                        </h3>
                        <div className="bg-surface border border-border/60 rounded-2xl overflow-hidden shadow-sm">
                            <table className="w-full text-left border-collapse">
                                <thead>
                                    <tr className="border-b border-border/50 bg-background-light/50 text-xs font-bold text-text-secondary uppercase tracking-wider">
                                        <th className="px-6 py-3">Documento</th>
                                        <th className="px-6 py-3">Tipo Definido</th>
                                        <th className="px-6 py-3">Status</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-border/40">
                                    {queuedDocs.map(doc => (
                                        <tr key={doc.id} className="hover:bg-background-light/30">
                                            <td className="px-6 py-3 text-sm text-text-main">{doc.filename}</td>
                                            <td className="px-6 py-3">
                                                <span className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded text-xs font-medium border border-blue-100">
                                                    {doc.doc_type}
                                                </span>
                                            </td>
                                            <td className="px-6 py-3">
                                                <span className="text-xs text-text-muted flex items-center gap-1">
                                                    <span className="size-1.5 bg-blue-400 rounded-full animate-pulse"></span>
                                                    Aguardando Batch
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}
            </div>

            {/* Modal */}
            <ReviewModal
                isOpen={!!selectedDoc}
                onClose={() => setSelectedDoc(null)}
                docId={selectedDoc?.id}
                filename={selectedDoc?.filename}
                initialDocType={selectedDoc?.doc_type}
                onSuccess={handleSuccess}
            />
        </div>
    );
};

export default StagingPage;
