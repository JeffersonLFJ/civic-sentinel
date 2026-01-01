import React, { useState, useEffect } from 'react';

export const ScanModal = ({ isOpen, onClose, onSuccess }) => {
    const [files, setFiles] = useState([]);
    const [loading, setLoading] = useState(false);
    const [processing, setProcessing] = useState(false);
    const [tags, setTags] = useState('');
    const [selection, setSelection] = useState({});
    const [docTypes, setDocTypes] = useState({}); // Per-file docType

    // Batch Controls
    const [globalDocType, setGlobalDocType] = useState('documento');

    useEffect(() => {
        if (isOpen) {
            fetchFiles();
        } else {
            setFiles([]);
            setSelection({});
            setDocTypes({});
            setTags('');
            setGlobalDocType('documento');
        }
    }, [isOpen]);

    const fetchFiles = async () => {
        setLoading(true);
        try {
            const res = await fetch('/api/admin/ingest/list');
            const data = await res.json();
            if (data.status === 'success') {
                const fetchedFiles = data.files || [];
                setFiles(fetchedFiles);

                // Auto select all by default
                const initialSel = {};
                const initialTypes = {};

                fetchedFiles.forEach(f => {
                    initialSel[f.filename] = true;
                    // Auto-guess type? For now default to 'documento' or based on extension?
                    // Safe default: documento
                    initialTypes[f.filename] = 'documento';
                });
                setSelection(initialSel);
                setDocTypes(initialTypes);
            }
        } catch (error) {
            console.error("Failed to fetch local files", error);
        } finally {
            setLoading(false);
        }
    };

    const toggleSelectAll = () => {
        const allSelected = files.length > 0 && files.every(f => selection[f.filename]);
        const newSel = {};
        files.forEach(f => newSel[f.filename] = !allSelected);
        setSelection(newSel);
    };

    const applyGlobalType = () => {
        const newTypes = { ...docTypes };
        files.filter(f => selection[f.filename]).forEach(f => {
            newTypes[f.filename] = globalDocType;
        });
        setDocTypes(newTypes);
    };

    const handleProcess = async () => {
        const itemsToProcess = files
            .filter(f => selection[f.filename])
            .map(f => ({
                filename: f.filename,
                doc_type: docTypes[f.filename] || 'documento',
                sphere: 'unknown',
                tags: tags
            }));

        if (itemsToProcess.length === 0) return;

        setProcessing(true);

        try {
            const res = await fetch('/api/admin/ingest/process', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ items: itemsToProcess })
            });

            const data = await res.json();
            if (data.status === 'success') {
                onSuccess();
                onClose();
            } else {
                alert(`Erro: ${data.detail}`);
            }
        } catch (e) {
            alert("Erro ao processar arquivos: " + e.message);
        } finally {
            setProcessing(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
            <div className="bg-surface border border-border rounded-2xl shadow-2xl w-full max-w-4xl overflow-hidden animate-in fade-in zoom-in-95 duration-200 flex flex-col max-h-[90vh]">
                <div className="px-6 py-4 border-b border-border flex justify-between items-center bg-background-light/50">
                    <div>
                        <h3 className="font-bold text-lg text-text-main flex items-center gap-2">
                            <span className="material-symbols-outlined text-primary">folder_open</span>
                            Scan Local (Quarentena)
                        </h3>
                        <p className="text-xs text-text-muted mt-0.5">Arquivos encontrados em <span className="font-mono bg-background border border-border/50 px-1 rounded">data/ingest</span></p>
                    </div>
                    <button onClick={onClose} className="text-text-secondary hover:text-text-main transition-colors">
                        <span className="material-symbols-outlined">close</span>
                    </button>
                </div>

                {/* Batch Actions Toolbar */}
                <div className="p-4 border-b border-border bg-background-light/30 flex flex-wrap items-center gap-4">
                    <button
                        onClick={toggleSelectAll}
                        className="text-xs font-semibold text-primary hover:text-primary-hover flex items-center gap-1">
                        <span className="material-symbols-outlined text-[16px]">
                            {files.length > 0 && files.every(f => selection[f.filename]) ? "check_box" : "check_box_outline_blank"}
                        </span>
                        Selecionar Todos
                    </button>

                    <div className="h-4 w-px bg-border mx-2"></div>

                    <div className="flex items-center gap-2">
                        <span className="text-xs font-semibold text-text-muted uppercase">Aplicar Tipo:</span>
                        <select
                            className="bg-background border border-border rounded px-2 py-1 text-xs outline-none focus:ring-1 focus:ring-primary"
                            value={globalDocType}
                            onChange={(e) => setGlobalDocType(e.target.value)}
                        >
                            <option value="documento">Documento (Geral)</option>
                            <option value="legislacao">Lei / Legislação</option>
                            <option value="diario">Diário Oficial</option>
                            <option value="tabela">Tabela (Dados)</option>
                        </select>
                        <button
                            onClick={applyGlobalType}
                            className="text-xs bg-white border border-border hover:bg-gray-50 px-2 py-1 rounded shadow-sm text-text-main font-medium">
                            Aplicar à Seleção
                        </button>
                    </div>

                    <div className="flex-1"></div>

                    <div className="flex items-center gap-2 px-3 py-1 bg-white border border-border rounded-lg shadow-sm">
                        <span className="text-xs font-semibold text-text-muted uppercase">Tags Globais:</span>
                        <input
                            type="text"
                            value={tags}
                            onChange={(e) => setTags(e.target.value)}
                            placeholder="Ex: urgente, análise..."
                            className="w-32 bg-transparent text-sm outline-none"
                        />
                    </div>
                </div>

                {/* File List */}
                <div className="flex-1 overflow-y-auto p-0 min-h-[300px]">
                    {loading ? (
                        <div className="p-10 text-center text-text-muted">Escaneando pasta...</div>
                    ) : files.length === 0 ? (
                        <div className="p-10 text-center text-text-muted">
                            <span className="material-symbols-outlined text-[48px] mb-2 opacity-20">folder_off</span>
                            <p>Nenhum arquivo encontrado em data/ingest.</p>
                        </div>
                    ) : (
                        <table className="w-full text-left border-collapse">
                            <thead className="sticky top-0 bg-background-light border-b border-border text-xs font-semibold text-text-secondary uppercase tracking-wider z-10">
                                <tr>
                                    <th className="px-4 py-3 w-10 text-center">
                                        {/* Header Checkbox optional/redundant with toggle button */}
                                    </th>
                                    <th className="px-4 py-3">Arquivo</th>
                                    <th className="px-4 py-3 w-48">Tipo de Documento</th>
                                    <th className="px-4 py-3 w-32 text-right">Tamanho</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-border/40">
                                {files.map((file) => (
                                    <tr key={file.filename} className={`hover:bg-background-light/50 transition-colors ${selection[file.filename] ? 'bg-primary/5' : ''}`}>
                                        <td className="px-4 py-3 text-center">
                                            <input
                                                type="checkbox"
                                                checked={!!selection[file.filename]}
                                                onChange={() => setSelection(prev => ({ ...prev, [file.filename]: !prev[file.filename] }))}
                                                className="rounded border-border text-primary focus:ring-primary/20 cursor-pointer size-4"
                                            />
                                        </td>
                                        <td className="px-4 py-3">
                                            <div className="flex flex-col">
                                                <span className="text-sm font-medium text-text-main line-clamp-1" title={file.filename}>{file.filename}</span>
                                                <span className="text-[10px] text-text-muted font-mono bg-gray-100 border px-1 rounded w-fit mt-1">{file.suggested_type}</span>
                                            </div>
                                        </td>
                                        <td className="px-4 py-3">
                                            <select
                                                className="w-full bg-white border border-border rounded px-2 py-1.5 text-xs outline-none focus:ring-1 focus:ring-primary"
                                                value={docTypes[file.filename] || 'documento'}
                                                onChange={(e) => setDocTypes(prev => ({ ...prev, [file.filename]: e.target.value }))}
                                                disabled={!selection[file.filename]}
                                            >
                                                <option value="documento">Documento (Geral)</option>
                                                <option value="legislacao">Lei / Legislação</option>
                                                <option value="diario">Diário Oficial</option>
                                                <option value="tabela">Tabela (Dados)</option>
                                            </select>
                                        </td>
                                        <td className="px-4 py-3 text-right text-xs text-text-muted font-mono">
                                            {(file.size / 1024).toFixed(1)} KB
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>

                <div className="px-6 py-4 bg-background-light/30 border-t border-border flex justify-between items-center">
                    <div className="text-xs text-text-muted">
                        {Object.values(selection).filter(Boolean).length} de {files.length} arquivos selecionados
                    </div>
                    <div className="flex gap-3">
                        <button onClick={onClose} className="px-4 py-2 rounded-lg text-sm font-semibold text-text-secondary hover:bg-background-light border border-transparent hover:border-border transition-all">Cancelar</button>
                        <button
                            onClick={handleProcess}
                            disabled={files.length === 0 || processing || Object.values(selection).filter(Boolean).length === 0}
                            className="px-6 py-2 rounded-lg text-sm font-semibold bg-primary text-white hover:bg-primary-hover disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-primary/20 transition-all flex items-center gap-2"
                        >
                            {processing ? 'Processando...' : `Importar (${Object.values(selection).filter(Boolean).length})`}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};
