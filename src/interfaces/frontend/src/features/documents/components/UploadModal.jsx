import React, { useState, useEffect } from 'react';
import { ProgressBar } from '../../../components/ui/ProgressBar';

export const UploadModal = ({ isOpen, onClose, onSuccess }) => {
    const [tags, setTags] = useState('');
    const [docType, setDocType] = useState('documento');
    const [dragging, setDragging] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [progress, setProgress] = useState(0);
    const [statusMsg, setStatusMsg] = useState('');
    const [customFilename, setCustomFilename] = useState(''); // New state for renaming
    const [file, setFile] = useState(null); // Missing state restored

    useEffect(() => {
        if (!isOpen) {
            setFile(null);
            setCustomFilename('');
            setTags('');
            setDocType('documento');
            setProgress(0);
            setStatusMsg('');
        }
    }, [isOpen]);

    // When file changes, reset custom name to original name
    useEffect(() => {
        if (file) {
            setCustomFilename(file.name);
        }
    }, [file]);

    const handleDrop = (e) => {
        e.preventDefault();
        setDragging(false);
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            setFile(e.dataTransfer.files[0]);
        }
    };

    const handleUpload = async () => {
        if (!file) return;

        setUploading(true);
        setStatusMsg('Enviando arquivo...');
        setProgress(10);

        // ...

        const progressInterval = setInterval(() => {
            setProgress((prev) => (prev >= 90 ? prev : prev + 5));
        }, 500);

        const formData = new FormData();
        formData.append('file', file);
        formData.append('tags', tags);
        formData.append('source', 'user_upload');
        formData.append('doc_type', docType);

        // Send custom filename if different
        if (customFilename && customFilename.trim() !== file.name) {
            formData.append('custom_filename', customFilename.trim());
        }

        try {
            const res = await fetch('/api/upload/', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();

            clearInterval(progressInterval);
            setProgress(100);
            setStatusMsg('Concluído!');

            if (res.ok) {
                setTimeout(() => {
                    onSuccess();
                    onClose();
                }, 800);
            } else {
                alert(`Erro: ${data.detail || 'Falha no upload'}`);
                setUploading(false);
            }
        } catch (error) {
            clearInterval(progressInterval);
            console.error(error);
            alert("Erro de conexão ao enviar arquivo.");
            setUploading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
            <div className="bg-surface border border-border rounded-2xl shadow-2xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in-95 duration-200">
                <div className="px-6 py-4 border-b border-border flex justify-between items-center bg-background-light/50">
                    <h3 className="font-bold text-lg text-text-main">Upload de Documento (Quarentena)</h3>
                    <button onClick={onClose} disabled={uploading} className="text-text-secondary hover:text-text-main transition-colors disabled:opacity-50">
                        <span className="material-symbols-outlined">close</span>
                    </button>
                </div>

                <div className="p-6 space-y-4">
                    {/* Dropzone */}
                    {!uploading ? (
                        <>
                            <div
                                className={`border-2 border-dashed rounded-xl p-8 text-center transition-all ${dragging ? 'border-primary bg-primary-soft/50' : 'border-border hover:border-primary/50 hover:bg-background-light'
                                    }`}
                                onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
                                onDragLeave={() => setDragging(false)}
                                onDrop={handleDrop}
                            >
                                {file ? (
                                    <div className="flex flex-col items-center gap-2">
                                        <div className="size-12 bg-emerald-50 text-emerald-600 rounded-full flex items-center justify-center mb-2">
                                            <span className="material-symbols-outlined text-[24px]">description</span>
                                        </div>
                                        <p className="text-sm font-medium text-text-main">{file.name}</p>
                                        <p className="text-xs text-text-muted">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                                        <button onClick={(e) => { e.stopPropagation(); setFile(null); }} className="text-xs text-red-500 hover:underline mt-2">Remover / Trocar</button>
                                    </div>
                                ) : (
                                    <div className="flex flex-col items-center gap-2 cursor-pointer relative">
                                        <input
                                            type="file"
                                            className="absolute inset-0 opacity-0 cursor-pointer"
                                            onChange={(e) => setFile(e.target.files[0])}
                                            accept=".pdf,.txt,.html"
                                        />
                                        <span className="material-symbols-outlined text-[32px] text-text-muted mb-2">cloud_upload</span>
                                        <p className="text-sm font-medium text-text-secondary">Arraste um arquivo ou clique aqui</p>
                                        <p className="text-xs text-text-muted">PDF, TXT, HTML (Máx 50MB)</p>
                                    </div>
                                )}
                            </div>

                            {file && (
                                <div className="space-y-1.5 animate-in slide-in-from-top-2 duration-200">
                                    <label className="text-xs font-semibold text-text-secondary uppercase tracking-wider flex items-center gap-1">
                                        Nome do Arquivo
                                        <span className="text-red-500">*</span>
                                    </label>
                                    <div className="flex items-center gap-2">
                                        <input
                                            type="text"
                                            value={customFilename}
                                            onChange={(e) => setCustomFilename(e.target.value)}
                                            className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm text-text-main focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none"
                                        />
                                        <span className="text-xs text-text-muted whitespace-nowrap hidden sm:block">
                                            .{file.name.split('.').pop()}
                                        </span>
                                    </div>
                                </div>
                            )}

                            <div className="space-y-1.5">
                                <label className="text-xs font-semibold text-text-secondary uppercase tracking-wider flex items-center gap-1">
                                    Tipo de Documento
                                    <span className="text-red-500">*</span>
                                </label>
                                <select
                                    value={docType}
                                    onChange={(e) => setDocType(e.target.value)}
                                    className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm text-text-main focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none appearance-none bg-no-repeat bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM2YjcyODAiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cG9seWxpbmUgcG9pbnRzPSI2IDkgMTIgMTUgMTggOSI+PC9wb2x5bGluZT48L3N2Zz4=')] bg-[right_0.5rem_center] bg-[length:1.25em_1.25em]"
                                >
                                    <option value="documento">Documento (Geral)</option>
                                    <option value="legislacao">Lei / Legislação</option>
                                    <option value="tabela">Tabela (Dados)</option>
                                    <option value="diario">Diário Oficial</option>
                                </select>
                            </div>

                            <div className="space-y-1.5">
                                <label className="text-xs font-semibold text-text-secondary uppercase tracking-wider flex items-center gap-1">
                                    Tags (Opcional)
                                    <span className="material-symbols-outlined text-[14px] text-text-muted" title="Para organização apenas na quarentena">info</span>
                                </label>
                                <input
                                    type="text"
                                    value={tags}
                                    onChange={(e) => setTags(e.target.value)}
                                    placeholder="Ex: saúde, urgente, projeto-lei (separados por vírgula)"
                                    className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm text-text-main focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none placeholder:text-text-muted"
                                />
                            </div>
                        </>
                    ) : (
                        <div className="py-10 flex flex-col items-center justify-center space-y-4">
                            <div className="size-16 bg-primary/10 rounded-full flex items-center justify-center animate-pulse">
                                <span className="material-symbols-outlined text-primary text-[32px] animate-spin">sync</span>
                            </div>
                            <div className="w-full max-w-xs text-center space-y-2">
                                <h4 className="font-bold text-text-main">Processando Documento</h4>
                                <ProgressBar progress={progress} label={statusMsg} />
                                <p className="text-xs text-text-muted">Isso pode levar alguns segundos a depender do tamanho do arquivo.</p>
                            </div>
                        </div>
                    )}
                </div>

                {!uploading && (
                    <div className="px-6 py-4 bg-background-light/30 border-t border-border flex justify-end gap-3">
                        <button onClick={onClose} className="px-4 py-2 rounded-lg text-sm font-semibold text-text-secondary hover:bg-background-light border border-transparent hover:border-border transition-all">Cancelar</button>
                        <button
                            onClick={handleUpload}
                            disabled={!file}
                            className="px-6 py-2 rounded-lg text-sm font-semibold bg-primary text-white hover:bg-primary-hover disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-primary/20 transition-all flex items-center gap-2"
                        >
                            Enviar para Quarentena
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};
