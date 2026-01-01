import React, { useState, useEffect } from 'react';

export const SettingsPage = () => {
    const [config, setConfig] = useState({
        llm_temperature: 0.1,
        llm_top_k: 40,
        llm_num_ctx: 4096,
        rag_top_k: 5,
        active_listening_threshold: 0.8,
        min_relevance_score: 0.4,
        ocr_validation_threshold: 80,
        system_prompt: '',
        intent_prompt: ''
    });
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        fetchSettings();
    }, []);

    const fetchSettings = async () => {
        setLoading(true);
        try {
            const res = await fetch('/api/admin/settings');
            const data = await res.json();
            setConfig(prev => ({ ...prev, ...data }));
        } catch (error) {
            console.error("Failed to fetch settings", error);
        } finally {
            setLoading(false);
        }
    };

    const handleChange = (e) => {
        const { name, value, type } = e.target;
        setConfig(prev => ({
            ...prev,
            [name]: type === 'number' || type === 'range' ? parseFloat(value) : value
        }));
    };

    const handleSave = async () => {
        setSaving(true);
        try {
            const res = await fetch('/api/admin/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });
            const data = await res.json();
            if (res.ok) {
                alert("Configurações salvas com sucesso!");
            } else {
                alert(`Erro ao salvar: ${data.detail}`);
            }
        } catch (error) {
            alert("Erro de conexão ao salvar.");
        } finally {
            setSaving(false);
        }
    };

    const handlePurge = async () => {
        const code = prompt("🚨 ATENÇÃO: Isso apagará TODA a memória vetorial (ChromaDB). Os documentos continuarão no banco de dados SQLite, mas não estarão mais buscáveis no Chat até serem reindexados.\n\nPara confirmar, digite 'DELETAR':");
        if (code !== 'DELETAR') return;

        try {
            const res = await fetch('/api/admin/settings/purge_cache', { method: 'POST' });
            const data = await res.json();
            alert(data.message || (res.ok ? "Cache purgado." : "Erro ao purgar."));
        } catch (e) {
            alert("Erro de conexão.");
        }
    };

    if (loading) return <div className="p-10 text-center text-text-muted">Carregando Cérebro...</div>;

    return (
        <div className="flex-1 flex flex-col bg-pattern h-full overflow-hidden">
            {/* Header */}
            <div className="flex-none px-10 py-8 border-b border-border bg-white/60 backdrop-blur-md z-10 sticky top-0 shadow-sm flex justify-between items-start">
                <div>
                    <h1 className="text-2xl font-bold text-text-main tracking-tight font-display mb-1">Cérebro & Configurações</h1>
                    <p className="text-text-secondary text-sm font-medium">Ajuste fino dos parâmetros cognitivos da IA e do motor de busca.</p>
                </div>
                <button
                    onClick={handleSave}
                    disabled={saving}
                    className="flex items-center gap-2 px-6 py-2 bg-primary hover:bg-primary-hover text-white rounded-lg text-sm font-semibold transition-all shadow-lg shadow-primary/20 hover:shadow-primary/30 active:scale-95 disabled:opacity-50">
                    <span className="material-symbols-outlined">{saving ? 'sync' : 'save'}</span>
                    {saving ? 'Salvando...' : 'Salvar Alterações'}
                </button>
            </div>

            {/* Content Scroller */}
            <div className="flex-1 overflow-y-auto p-10">
                <div className="max-w-4xl mx-auto space-y-8 pb-20">

                    {/* LLM Settings */}
                    <section className="bg-surface border border-border rounded-xl p-6 shadow-sm">
                        <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border/50">
                            <span className="material-symbols-outlined text-primary text-[28px]">psychology</span>
                            <h2 className="text-lg font-bold text-text-main">Modelo de Linguagem (LLM)</h2>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                            <div className="space-y-4">
                                <div>
                                    <div className="flex justify-between mb-1">
                                        <label className="text-sm font-medium text-text-main">Temperatura (Criatividade)</label>
                                        <span className="text-sm font-mono text-primary font-bold">{config.llm_temperature}</span>
                                    </div>
                                    <input
                                        type="range" name="llm_temperature" min="0" max="1" step="0.1"
                                        value={config.llm_temperature} onChange={handleChange}
                                        className="w-full h-2 bg-background-light rounded-lg appearance-none cursor-pointer accent-primary"
                                    />
                                    <p className="text-xs text-text-muted mt-1">Baixo = Preciso/Robótico. Alto = Criativo/Inesperado.</p>
                                </div>

                                <div>
                                    <div className="flex justify-between mb-1">
                                        <label className="text-sm font-medium text-text-main">Top-K Generation</label>
                                        <span className="text-sm font-mono text-primary font-bold">{config.llm_top_k}</span>
                                    </div>
                                    <input
                                        type="number" name="llm_top_k" min="1" max="100"
                                        value={config.llm_top_k} onChange={handleChange}
                                        className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm"
                                    />
                                </div>
                            </div>

                            <div className="space-y-4">
                                <div className="space-y-1.5">
                                    <label className="text-sm font-medium text-text-main">Context Window</label>
                                    <select
                                        name="llm_num_ctx"
                                        value={config.llm_num_ctx}
                                        onChange={handleChange}
                                        className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-primary"
                                    >
                                        <option value="2048">2048 Tokens (Rápido)</option>
                                        <option value="4096">4096 Tokens (Padrão)</option>
                                        <option value="8192">8192 Tokens (Memória Longa)</option>
                                        <option value="16384">16384 Tokens (Extremo)</option>
                                    </select>
                                    <p className="text-xs text-text-muted">Tamanho da "memória de trabalho" ativa do modelo.</p>
                                </div>
                            </div>
                        </div>

                        <div className="mt-6">
                            <label className="text-sm font-medium text-text-main mb-2 block">System Prompt (Persona)</label>
                            <textarea
                                name="system_prompt"
                                value={config.system_prompt}
                                onChange={handleChange}
                                rows="6"
                                className="w-full bg-background border border-border rounded-lg p-4 text-sm font-mono text-text-secondary focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none"
                                placeholder="# Instruções do Sentinela..."
                            ></textarea>
                        </div>
                    </section>

                    {/* RAG Settings */}
                    <section className="bg-surface border border-border rounded-xl p-6 shadow-sm">
                        <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border/50">
                            <span className="material-symbols-outlined text-accent-blue text-[28px]">manage_search</span>
                            <h2 className="text-lg font-bold text-text-main">Motor de Busca (RAG)</h2>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                            <div>
                                <div className="flex justify-between mb-1">
                                    <label className="text-sm font-medium text-text-main">Retrieval Count (Top-K)</label>
                                    <span className="text-sm font-mono text-accent-blue font-bold">{config.rag_top_k}</span>
                                </div>
                                <input
                                    type="range" name="rag_top_k" min="1" max="20" step="1"
                                    value={config.rag_top_k} onChange={handleChange}
                                    className="w-full h-2 bg-background-light rounded-lg appearance-none cursor-pointer accent-accent-blue"
                                />
                                <p className="text-xs text-text-muted mt-1">Número de trechos de documentos lidos por pergunta.</p>
                            </div>

                            <div>
                                <div className="flex justify-between mb-1">
                                    <label className="text-sm font-medium text-text-main">Min Relevance Score</label>
                                    <span className="text-sm font-mono text-accent-blue font-bold">{config.min_relevance_score}</span>
                                </div>
                                <input
                                    type="range" name="min_relevance_score" min="0" max="1" step="0.05"
                                    value={config.min_relevance_score} onChange={handleChange}
                                    className="w-full h-2 bg-background-light rounded-lg appearance-none cursor-pointer accent-accent-blue"
                                />
                                <p className="text-xs text-text-muted mt-1">Corte mínimo de qualidade. Documentos abaixo dessa nota são ignorados.</p>
                            </div>

                            <div>
                                <div className="flex justify-between mb-1">
                                    <label className="text-sm font-medium text-text-main">Limiar de Escuta Ativa</label>
                                    <span className="text-sm font-mono text-accent-blue font-bold">{config.active_listening_threshold}</span>
                                </div>
                                <input
                                    type="range" name="active_listening_threshold" min="0" max="1" step="0.1"
                                    value={config.active_listening_threshold} onChange={handleChange}
                                    className="w-full h-2 bg-background-light rounded-lg appearance-none cursor-pointer accent-accent-blue"
                                />
                                <p className="text-xs text-text-muted mt-1">Se a ambiguidade da pergunta for maior que isso, o Sentinela pergunta de volta.</p>
                            </div>
                        </div>
                    </section>

                    {/* Models & Ingestion */}
                    <section className="bg-surface border border-border rounded-xl p-6 shadow-sm">
                        <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border/50">
                            <span className="material-symbols-outlined text-primary text-[28px]">settings_system_daydream</span>
                            <h2 className="text-lg font-bold text-text-main">Modelos & Ingestão</h2>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-6">
                            <div>
                                <label className="text-sm font-medium text-text-main mb-1 block">Modelo LLM (Texto)</label>
                                <input
                                    type="text" name="llm_model"
                                    value={config.llm_model || ''} onChange={handleChange}
                                    className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm font-mono"
                                    placeholder="ex: gemma2:2b"
                                />
                                <p className="text-xs text-text-muted mt-1">Nome do modelo no Ollama.</p>
                            </div>
                            <div>
                                <label className="text-sm font-medium text-text-main mb-1 block">Modelo Vision (Imagem)</label>
                                <input
                                    type="text" name="vision_model"
                                    value={config.vision_model || ''} onChange={handleChange}
                                    className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm font-mono"
                                    placeholder="ex: llava"
                                />
                                <p className="text-xs text-text-muted mt-1">Usado para descrever imagens em documentos.</p>
                            </div>
                        </div>

                        <div className="bg-yellow-50/50 border border-yellow-100 rounded-lg p-4">
                            <h3 className="text-sm font-bold text-yellow-800 mb-3 flex items-center gap-2">
                                <span className="material-symbols-outlined text-[18px]">warning</span>
                                Parâmetros de Vetorização (Requer Re-indexação)
                            </h3>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                <div>
                                    <label className="text-xs font-bold text-text-secondary uppercase mb-1 block">Chunk Size</label>
                                    <input
                                        type="number" name="chunk_size"
                                        value={config.chunk_size || 3000} onChange={handleChange}
                                        className="w-full bg-white border border-border rounded px-2 py-1 text-sm"
                                    />
                                </div>
                                <div>
                                    <label className="text-xs font-bold text-text-secondary uppercase mb-1 block">Overlap</label>
                                    <input
                                        type="number" name="chunk_overlap"
                                        value={config.chunk_overlap || 500} onChange={handleChange}
                                        className="w-full bg-white border border-border rounded px-2 py-1 text-sm"
                                    />
                                </div>
                                <div>
                                    <label className="text-xs font-bold text-text-secondary uppercase mb-1 block">OCR Threshold</label>
                                    <input
                                        type="number" name="ocr_validation_threshold"
                                        value={config.ocr_validation_threshold || 80} onChange={handleChange}
                                        className="w-full bg-white border border-border rounded px-2 py-1 text-sm"
                                    />
                                </div>
                            </div>
                        </div>
                    </section>

                    {/* Danger Zone */}
                    <section className="bg-red-50/50 border border-red-200 rounded-xl p-6 shadow-sm">
                        <div className="flex items-center gap-3 mb-4">
                            <span className="material-symbols-outlined text-red-500 text-[28px]">dangerous</span>
                            <h2 className="text-lg font-bold text-red-700">Zona de Perigo</h2>
                        </div>
                        <p className="text-sm text-red-600 mb-6">Ações irreversíveis que afetam o funcionamento do sistema.</p>

                        <div className="flex items-center justify-between bg-white p-4 rounded-lg border border-red-100">
                            <div>
                                <h4 className="font-bold text-text-main text-sm">Purgar Cache Vetorial</h4>
                                <p className="text-xs text-text-muted">Apaga todos os embeddings do ChromaDB. Necessário reindexar tudo.</p>
                            </div>
                            <button
                                onClick={handlePurge}
                                className="px-4 py-2 bg-red-100 hover:bg-red-200 text-red-700 text-xs font-bold rounded-lg transition-colors border border-red-200">
                                Purgar Cache
                            </button>
                        </div>
                    </section>

                </div>
            </div>
        </div>
    );
};

export default SettingsPage;
