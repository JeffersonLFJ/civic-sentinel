import React, { useState, useEffect } from 'react';

export const InspectorPage = () => {
    const [docs, setDocs] = useState([]);
    const [selectedDocId, setSelectedDocId] = useState(null);
    const [chunks, setChunks] = useState([]);
    const [loadingDocs, setLoadingDocs] = useState(true);
    const [loadingChunks, setLoadingChunks] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        fetchDocs();
    }, []);

    useEffect(() => {
        if (selectedDocId) {
            fetchChunks(selectedDocId);
        } else {
            setChunks([]);
        }
    }, [selectedDocId]);

    const fetchDocs = async () => {
        setLoadingDocs(true);
        try {
            const res = await fetch('/api/documents/?limit=100');
            const data = await res.json();
            const list = Array.isArray(data) ? data : (data.data || []);
            setDocs(list);
        } catch (error) {
            console.error("Failed to fetch docs", error);
        } finally {
            setLoadingDocs(false);
        }
    };

    const fetchChunks = async (id) => {
        setLoadingChunks(true);
        try {
            const res = await fetch(`/api/admin/inspect/${id}`);
            const data = await res.json();
            setChunks(data.chunks || []);
        } catch (error) {
            console.error("Failed to fetch chunks", error);
            setChunks([]);
        } finally {
            setLoadingChunks(false);
        }
    };

    const filteredDocs = docs.filter(d =>
        d.filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
        d.id.includes(searchTerm)
    );

    return (
        <div className="flex-1 flex bg-pattern h-full overflow-hidden">
            {/* Sidebar List */}
            <aside className="w-80 border-r border-border bg-surface flex flex-col z-10 shrink-0">
                <div className="p-4 border-b border-border bg-background-light/50">
                    <h2 className="text-lg font-bold text-text-main mb-1">Documentos</h2>
                    <p className="text-xs text-text-muted mb-3">Selecione para inspecionar vetores.</p>
                    <div className="relative">
                        <span className="absolute inset-y-0 left-0 flex items-center pl-2 text-text-muted">
                            <span className="material-symbols-outlined text-[18px]">search</span>
                        </span>
                        <input
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full bg-background border border-border rounded-lg pl-8 pr-3 py-2 text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
                            placeholder="Buscar arquivo..."
                        />
                    </div>
                </div>

                <div className="flex-1 overflow-y-auto p-2 space-y-1">
                    {loadingDocs ? (
                        <div className="p-4 text-center text-text-muted text-sm">Carregando lista...</div>
                    ) : filteredDocs.length === 0 ? (
                        <div className="p-4 text-center text-text-muted text-sm">Nenhum documento.</div>
                    ) : (
                        filteredDocs.map(doc => (
                            <div
                                key={doc.id}
                                onClick={() => setSelectedDocId(doc.id)}
                                className={`p-3 rounded-lg cursor-pointer transition-all border ${selectedDocId === doc.id
                                        ? 'bg-primary/10 border-primary/30 shadow-sm'
                                        : 'border-transparent hover:bg-background-light border-hover:border-border/50'
                                    }`}
                            >
                                <p className={`text-sm font-semibold truncate ${selectedDocId === doc.id ? 'text-primary' : 'text-text-main'}`}>
                                    {doc.filename}
                                </p>
                                <div className="flex items-center justify-between mt-1">
                                    <span className="text-[10px] uppercase font-bold text-text-muted tracking-wide">{doc.source}</span>
                                    <span className="text-[10px] font-mono text-text-muted opacity-60">{doc.id.substring(0, 6)}...</span>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </aside>

            {/* Main Content: Chunks Viewer */}
            <main className="flex-1 flex flex-col overflow-hidden bg-background relative">
                {!selectedDocId ? (
                    <div className="flex-1 flex flex-col items-center justify-center text-text-muted p-10 text-center opacity-60">
                        <span className="material-symbols-outlined text-[64px] mb-4">manage_search</span>
                        <h3 className="text-xl font-medium text-text-main">Inspetor de Dados Vetoriais</h3>
                        <p className="max-w-md mt-2">Selecione um documento na barra lateral para visualizar como ele foi fragmentado (chunking) e armazenado no ChromaDB.</p>
                    </div>
                ) : (
                    <>
                        <div className="flex-none px-8 py-6 border-b border-border bg-white/60 backdrop-blur-md z-10 sticky top-0 flex justify-between items-center shadow-sm">
                            <div>
                                <h1 className="text-xl font-bold text-text-main font-mono">{selectedDocId}</h1>
                                <p className="text-sm text-text-secondary">Visualizando chunks indexados.</p>
                            </div>
                            <div className="flex items-center gap-4">
                                <div className="text-right">
                                    <p className="text-2xl font-bold text-primary font-mono leading-none">{chunks.length}</p>
                                    <p className="text-[10px] uppercase font-bold text-text-muted tracking-wider">Chunks</p>
                                </div>
                            </div>
                        </div>

                        <div className="flex-1 overflow-y-auto p-8">
                            {loadingChunks ? (
                                <div className="p-10 text-center text-text-muted">Carregando shards do ChromaDB...</div>
                            ) : chunks.length === 0 ? (
                                <div className="p-10 text-center text-red-500 bg-red-50 rounded-xl border border-red-100">
                                    <p className="font-bold">Nenhum chunk encontrado.</p>
                                    <p className="text-sm mt-1">Este documento pode não ter sido processado corretamente ou ainda está na fila de indexação.</p>
                                </div>
                            ) : (
                                <div className="grid gap-6">
                                    {chunks.map((chunk, idx) => (
                                        <div key={idx} className="bg-surface border border-border rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow group">
                                            <div className="flex justify-between items-start mb-3 pb-3 border-b border-border/50">
                                                <div className="flex items-center gap-2">
                                                    <span className="size-6 bg-background-light text-text-muted rounded flex items-center justify-center font-mono text-xs border border-border">
                                                        #{idx}
                                                    </span>
                                                    <span className="px-2 py-0.5 bg-blue-50 text-blue-600 rounded text-[10px] font-bold uppercase border border-blue-100">
                                                        Length: {chunk.full_length}
                                                    </span>
                                                </div>
                                                <div className="text-[10px] text-text-muted font-mono bg-background px-2 py-1 rounded border border-border truncate max-w-[50%]">
                                                    {JSON.stringify(chunk.metadata)}
                                                </div>
                                            </div>
                                            <div className="relative">
                                                <p className="font-mono text-xs text-text-secondary whitespace-pre-wrap leading-relaxed bg-background/50 p-3 rounded-lg border border-border/50">
                                                    {chunk.content}
                                                </p>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </>
                )}
            </main>
        </div>
    );
};

export default InspectorPage;
