import React, { useState, useEffect } from 'react';

export const ReviewModal = ({ isOpen, onClose, docId, filename, initialDocType, onSuccess }) => {
    const [loading, setLoading] = useState(false);
    const [text, setText] = useState('');
    const [approving, setApproving] = useState(false);

    // Workflow State
    const [step, setStep] = useState(0); // 0: Classification, 1: Details
    const [isLegislation, setIsLegislation] = useState(false);

    // Form State
    const [sphere, setSphere] = useState('');
    const [docType, setDocType] = useState('lei_ordinaria');
    const [pubDate, setPubDate] = useState('');
    const [ementa, setEmenta] = useState(''); // Only for Legislation
    const [description, setDescription] = useState(''); // Only for Generic
    const [customTags, setCustomTags] = useState('');

    useEffect(() => {
        if (isOpen && docId) {
            fetchText();
            // Reset form
            setSphere('');
            setPubDate('');
            setEmenta('');
            setDescription('');
            setCustomTags('');

            // Auto-Classification Logic
            if (initialDocType && initialDocType !== 'pending_classification') {
                const legTypes = ['legislacao', 'diario', 'lei_ordinaria', 'decreto', 'portaria'];
                const isLeg = legTypes.includes(initialDocType);

                setIsLegislation(isLeg);
                setStep(1); // Skip classification step

                // Pre-fill type if possible
                if (isLeg) {
                    // map 'legislacao' to default 'lei_ordinaria' or keep if specific
                    setDocType(initialDocType === 'legislacao' ? 'lei_ordinaria' : initialDocType);
                    setSphere('municipal');
                } else {
                    setDocType(initialDocType === 'tabela' ? 'tabela' : 'generico');
                    setSphere('municipal'); // Default
                }
            } else {
                // Manual Classification needed
                setStep(0);
                setIsLegislation(false);
                setDocType('lei_ordinaria');
            }
        }
    }, [isOpen, docId, initialDocType]);

    const fetchText = async () => {
        setLoading(true);
        try {
            const res = await fetch(`/api/admin/staging/${docId}/text`);
            const data = await res.json();
            setText(data.text || '');
        } catch (error) {
            setText("Erro ao carregar texto.");
        } finally {
            setLoading(false);
        }
    };

    const handleSelectClassification = (isLeg) => {
        setIsLegislation(isLeg);
        setStep(1);
        if (isLeg) {
            setDocType('lei_ordinaria');
            setSphere('municipal'); // Default smart guess
        } else {
            setDocType('generico');
            setSphere('municipal');
        }
    };

    const handleApprove = async () => {
        // Validation Logic
        if (isLegislation) {
            if (!sphere || !docType || !pubDate || !ementa) {
                alert("Para Legislação/Atos, preencha: Esfera, Tipo, Data e Ementa.");
                return;
            }
        } else {
            // Generic validation is looser
            if (!description) {
                alert("Por favor, forneça uma breve descrição do documento.");
                return;
            }
        }

        setApproving(true);
        try {
            const payload = {
                sphere,
                doc_type: docType,
                publication_date: pubDate || null, // Optional for generic
                ementa: isLegislation ? ementa : null,
                description: isLegislation ? null : description,
                custom_tags: customTags
            };

            const res = await fetch(`/api/admin/staging/${docId}/approve`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await res.json();
            if (res.ok) {
                onSuccess();
                onClose();
            } else {
                alert(`Erro: ${data.detail || 'Falha ao aprovar'}`);
            }
        } catch (error) {
            alert("Erro de conexão.");
        } finally {
            setApproving(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <div className="bg-surface border border-border rounded-2xl shadow-2xl w-full max-w-6xl h-[90vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">

                {/* Header */}
                <div className="px-6 py-4 border-b border-border bg-background-light/50 flex justify-between items-center shrink-0">
                    <div>
                        <h3 className="font-bold text-lg text-text-main flex items-center gap-2">
                            <span className="material-symbols-outlined text-primary">rate_review</span>
                            Revisão de Documento
                        </h3>
                        <p className="text-xs text-text-muted mt-0.5 max-w-lg truncate">{filename}</p>
                    </div>
                    <button onClick={onClose} className="text-text-secondary hover:text-text-main transition-colors">
                        <span className="material-symbols-outlined">close</span>
                    </button>
                </div>

                {/* Content Grid */}
                <div className="flex-1 overflow-hidden grid grid-cols-1 lg:grid-cols-2">

                    {/* Left: Text Preview (Always Visible) */}
                    <div className="flex flex-col border-r border-border/50 bg-background/50">
                        <div className="px-4 py-2 border-b border-border/30 bg-background-light/30 flex justify-between items-center">
                            <span className="text-xs font-semibold text-text-secondary uppercase tracking-wider">Preview do OCR</span>
                            <span className="text-[10px] text-text-muted bg-surface border border-border/50 px-1.5 py-0.5 rounded">
                                {text.length} caracteres
                            </span>
                        </div>
                        <div className="flex-1 overflow-y-auto p-4 font-mono text-xs text-text-secondary leading-relaxed whitespace-pre-wrap select-text selection:bg-primary/20">
                            {loading ? (
                                <div className="flex items-center justify-center h-full text-text-muted">
                                    <span className="animate-pulse">Carregando texto...</span>
                                </div>
                            ) : (
                                text || <span className="text-text-muted italic">Nenhum texto extraído.</span>
                            )}
                        </div>
                    </div>

                    {/* Right: Metadata Form */}
                    <div className="flex flex-col bg-surface overflow-y-auto">

                        {step === 0 && (
                            <div className="flex-1 flex flex-col items-center justify-center p-10 text-center space-y-8">
                                <div>
                                    <h4 className="text-xl font-bold text-text-main mb-2">Classificação Inicial</h4>
                                    <p className="text-text-secondary">Que tipo de documento é este?</p>
                                </div>

                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full max-w-md">
                                    <button
                                        onClick={() => handleSelectClassification(true)}
                                        className="flex flex-col items-center gap-3 p-6 rounded-xl border-2 border-border hover:border-primary/50 hover:bg-primary-soft/10 transition-all group"
                                    >
                                        <div className="size-12 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center group-hover:scale-110 transition-transform">
                                            <span className="material-symbols-outlined text-[28px]">gavel</span>
                                        </div>
                                        <div>
                                            <span className="block font-bold text-text-main">Legislação / Oficial</span>
                                            <span className="text-xs text-text-muted">Leis, Decretos, Diários</span>
                                        </div>
                                    </button>

                                    <button
                                        onClick={() => handleSelectClassification(false)}
                                        className="flex flex-col items-center gap-3 p-6 rounded-xl border-2 border-border hover:border-orange-400/50 hover:bg-orange-50/50 transition-all group"
                                    >
                                        <div className="size-12 rounded-full bg-orange-50 text-orange-600 flex items-center justify-center group-hover:scale-110 transition-transform">
                                            <span className="material-symbols-outlined text-[28px]">description</span>
                                        </div>
                                        <div>
                                            <span className="block font-bold text-text-main">Documento Genérico</span>
                                            <span className="text-xs text-text-muted">Relatórios, Notas, Outros</span>
                                        </div>
                                    </button>
                                </div>
                            </div>
                        )}

                        {step === 1 && (
                            <div className="p-6 space-y-6">
                                <div className="flex items-center justify-between">
                                    <button onClick={() => setStep(0)} className="text-xs text-primary hover:underline flex items-center gap-1">
                                        <span className="material-symbols-outlined text-[14px]">arrow_back</span>
                                        Voltar
                                    </button>
                                    <span className="text-xs font-semibold uppercase tracking-wider text-text-muted">
                                        {isLegislation ? "Metadados Jurídicos" : "Metadados Gerais"}
                                    </span>
                                </div>

                                {/* LEGISLATION FORM */}
                                {isLegislation ? (
                                    <>
                                        <div className="space-y-1.5">
                                            <label className="text-sm font-medium text-text-main">Ementa (Resumo Oficial) <span className="text-red-500">*</span></label>
                                            <textarea
                                                value={ementa}
                                                onChange={(e) => setEmenta(e.target.value)}
                                                rows={4}
                                                className="w-full bg-background border border-border rounded-lg px-3 py-2.5 text-sm text-text-main focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all placeholder:text-text-muted/50"
                                                placeholder="Copie e cole a ementa da lei aqui..."
                                            />
                                        </div>

                                        <div className="grid grid-cols-2 gap-4">
                                            <div className="space-y-1.5">
                                                <label className="text-sm font-medium text-text-main">Esfera <span className="text-red-500">*</span></label>
                                                <select
                                                    value={sphere}
                                                    onChange={(e) => setSphere(e.target.value)}
                                                    className="w-full bg-background border border-border rounded-lg px-3 py-2.5 text-sm text-text-main focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none"
                                                >
                                                    <option value="municipal">Municipal</option>
                                                    <option value="estadual">Estadual</option>
                                                    <option value="federal">Federal</option>
                                                </select>
                                            </div>
                                            <div className="space-y-1.5">
                                                <label className="text-sm font-medium text-text-main">Tipo <span className="text-red-500">*</span></label>
                                                <select
                                                    value={docType}
                                                    onChange={(e) => setDocType(e.target.value)}
                                                    className="w-full bg-background border border-border rounded-lg px-3 py-2.5 text-sm text-text-main focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none"
                                                >
                                                    <option value="lei_ordinaria">Lei Ordinária</option>
                                                    <option value="lei_complementar">Lei Complementar</option>
                                                    <option value="decreto">Decreto</option>
                                                    <option value="portaria">Portaria</option>
                                                    <option value="resolucao">Resolução</option>
                                                    <option value="constituicao">Constituição / Emenda</option>
                                                    <option value="diario_oficial">Diário Oficial</option>
                                                </select>
                                            </div>
                                        </div>

                                        <div className="space-y-1.5">
                                            <label className="text-sm font-medium text-text-main">Data de Publicação <span className="text-red-500">*</span></label>
                                            <input
                                                type="date"
                                                value={pubDate}
                                                onChange={(e) => setPubDate(e.target.value)}
                                                className="w-full bg-background border border-border rounded-lg px-3 py-2.5 text-sm text-text-main focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none"
                                            />
                                        </div>
                                    </>
                                ) : (
                                    /* GENERIC FORM */
                                    <>
                                        <div className="space-y-1.5">
                                            <label className="text-sm font-medium text-text-main">Descrição Breve <span className="text-red-500">*</span></label>
                                            <textarea
                                                value={description}
                                                onChange={(e) => setDescription(e.target.value)}
                                                rows={4}
                                                className="w-full bg-background border border-border rounded-lg px-3 py-2.5 text-sm text-text-main focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all placeholder:text-text-muted/50"
                                                placeholder="Descreva o conteúdo deste documento para facilitar a busca..."
                                            />
                                        </div>
                                        <div className="space-y-1.5">
                                            <label className="text-sm font-medium text-text-main">Data (Opcional)</label>
                                            <input
                                                type="date"
                                                value={pubDate}
                                                onChange={(e) => setPubDate(e.target.value)}
                                                className="w-full bg-background border border-border rounded-lg px-3 py-2.5 text-sm text-text-main focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none"
                                            />
                                        </div>
                                    </>
                                )}

                                <div className="space-y-1.5">
                                    <label className="text-sm font-medium text-text-main">Tags Personalizadas (Opcional)</label>
                                    <input
                                        type="text"
                                        value={customTags}
                                        onChange={(e) => setCustomTags(e.target.value)}
                                        placeholder="Ex: saúde, fiscalização, urgente"
                                        className="w-full bg-background border border-border rounded-lg px-3 py-2.5 text-sm text-text-main focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none"
                                    />
                                    <p className="text-[10px] text-text-muted">Tags ajudam a organizar documentos descartáveis ou projetos específicos.</p>
                                </div>

                                <div className="pt-6 border-t border-border mt-4">
                                    <button
                                        onClick={handleApprove}
                                        disabled={approving}
                                        className="w-full py-3 rounded-xl font-bold bg-primary text-white hover:bg-primary-hover disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-primary/20 transition-all transform active:scale-[0.98] flex items-center justify-center gap-2"
                                    >
                                        {approving ? (
                                            <>
                                                <span className="size-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                                                Salvando...
                                            </>
                                        ) : (
                                            <>
                                                <span className="material-symbols-outlined">queue</span>
                                                Confirmar e Enviar para Fila
                                            </>
                                        )}
                                    </button>
                                    <p className="text-xs text-center text-text-muted mt-3">
                                        O documento será movido para o status "Aguardando Processamento".
                                    </p>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};
