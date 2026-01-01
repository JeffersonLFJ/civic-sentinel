import React, { useState, useEffect } from 'react';

import { ChatMessage } from '../../../components/ui/ChatMessage';

const StatCard = ({ icon, label, value, colorClass }) => (
    <div className="flex items-center gap-3 px-4 py-2 rounded-lg bg-white/80 border border-border/60 shadow-sm backdrop-blur-sm">
        <div className={`p-1.5 rounded-full ${colorClass}`}>
            <span className="material-symbols-outlined text-[20px]">{icon}</span>
        </div>
        <div className="flex flex-col">
            <span className="text-[10px] uppercase text-text-muted font-bold tracking-wider">{label}</span>
            <span className="text-sm font-mono font-bold text-text-main">{value}</span>
        </div>
    </div>
);

export const AuditoriaContent = ({ selectedId }) => {
    const [detail, setDetail] = useState(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (!selectedId) return;

        setLoading(true);
        fetch(`/api/admin/audit/${selectedId}`)
            .then(res => res.json())
            .then(data => {
                setDetail(data);
                setLoading(false);
            })
            .catch(err => {
                console.error("Failed to load details", err);
                setLoading(false);
            });
    }, [selectedId]);

    if (!selectedId) {
        return <div className="flex-1 flex items-center justify-center text-text-muted">Selecione uma interação para ver os detalhes.</div>;
    }

    if (loading || !detail) {
        return <div className="flex-1 flex items-center justify-center text-text-muted">Carregando detalhes...</div>;
    }

    // Parse helpers
    const displayId = `#${detail.id.toString().substring(0, 8)}`.toUpperCase();
    const sources = detail.sources_json || [];
    const reasoning = detail.reasoning_map || {};

    return (
        <div className="flex-1 flex flex-col bg-pattern h-full overflow-hidden">
            {/* Header */}
            <div className="flex-none px-10 py-6 border-b border-border bg-white/60 backdrop-blur-md z-10 sticky top-0 shadow-sm">
                <div className="flex items-start justify-between mb-6">
                    <div>
                        <div className="flex items-center gap-4 mb-2">
                            <h1 className="text-2xl font-bold text-text-main tracking-tight font-display">Detalhes da Auditoria</h1>
                            <span className="bg-surface text-text-secondary text-xs px-3 py-1 rounded-lg font-mono border border-border/60 shadow-sm">ID: {displayId}</span>
                        </div>
                        <p className="text-text-secondary text-sm ml-1 max-w-2xl font-medium leading-relaxed">
                            Visualizando a cadeia de raciocínio da Inteligência Artificial.
                        </p>
                    </div>
                </div>

                {/* Stats */}
                <div className="flex flex-wrap gap-4">
                    <StatCard icon="timer" label="Latência" value="N/A" colorClass="bg-blue-50 text-accent-blue" />
                    <StatCard icon="psychology" label="Confiança" value={`${(detail.confidence_score * 100).toFixed(1)}%`} colorClass="bg-primary-soft text-primary" />
                    <StatCard icon="token" label="Custo (Tokens)" value="-" colorClass="bg-purple-50 text-purple-500" />
                    <StatCard icon="gavel" label="Modelo" value={detail.details?.model || "Standard"} colorClass="bg-orange-50 text-accent-orange" />
                </div>
            </div>

            {/* Main Grid */}
            <div className="flex-1 overflow-y-auto p-10">
                <div className="grid grid-cols-1 xl:grid-cols-12 gap-8 max-w-[1600px] mx-auto">
                    {/* Column 1: Transcript */}
                    <div className="xl:col-span-7 flex flex-col gap-8">
                        <div className="flex items-center gap-2 mb-2">
                            <span className="material-symbols-outlined text-primary text-[20px]">chat_bubble</span>
                            <h3 className="text-sm font-bold uppercase tracking-wider text-text-secondary">Transcrição da Interação</h3>
                        </div>

                        <ChatMessage
                            sender="Usuário"
                            time={new Date(detail.timestamp).toLocaleTimeString()}
                            text={detail.query}
                            isAi={false}
                        />

                        <ChatMessage
                            sender="Sentinela AI"
                            time={new Date(detail.timestamp).toLocaleTimeString()}
                            isAi={true}
                            text={detail.response || "(Sem resposta)"}
                        />
                    </div>

                    {/* Column 2: Analysis/RAG */}
                    <div className="xl:col-span-5 flex flex-col gap-6">

                        {/* RAG Section */}
                        {sources.length > 0 && (
                            <div className="bg-surface border border-border/60 rounded-2xl overflow-hidden shadow-card">
                                <div className="px-6 py-4 border-b border-border/40 bg-background-light flex justify-between items-center">
                                    <div className="flex items-center gap-2">
                                        <span className="material-symbols-outlined text-primary text-[20px]">find_in_page</span>
                                        <h3 className="font-bold text-text-main text-sm">Fontes Recuperadas (RAG)</h3>
                                    </div>
                                    <span className="bg-white border border-border text-text-secondary text-[10px] px-2.5 py-1 rounded-full font-bold shadow-sm">{sources.length} DOCS</span>
                                </div>
                                <div className="p-5 space-y-6">
                                    {sources.map((src, idx) => (
                                        <div key={idx} className="group relative">
                                            <div className="flex justify-between text-xs mb-3">
                                                <span className="font-bold text-text-main flex items-center gap-2">
                                                    <div className="size-7 bg-primary-soft text-primary rounded-lg flex items-center justify-center border border-primary/10">
                                                        <span className="material-symbols-outlined text-[16px]">article</span>
                                                    </div>
                                                    {src.filename || "Documento"}
                                                </span>
                                                <span className="font-mono font-bold text-primary bg-primary-soft px-2 py-0.5 rounded text-[10px] border border-primary/10">
                                                    {src.relevance_score ? `${(src.relevance_score * 100).toFixed(0)}% Match` : 'Ref'}
                                                </span>
                                            </div>
                                            <p className="text-[13px] text-text-secondary leading-relaxed italic bg-background-light p-3 rounded-lg border border-border/50 line-clamp-3">
                                                "{src.content}"
                                            </p>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* CoT Section */}
                        {detail.details && (
                            <div className="bg-surface border border-border/60 rounded-2xl overflow-hidden shadow-card flex-1">
                                <div className="px-6 py-4 border-b border-border/40 bg-background-light flex justify-between items-center">
                                    <div className="flex items-center gap-2">
                                        <span className="material-symbols-outlined text-purple-500 text-[20px]">account_tree</span>
                                        <h3 className="font-bold text-text-main text-sm">Raio-X do Raciocínio (CoT)</h3>
                                    </div>
                                </div>
                                <div className="p-6 relative">
                                    <div className="absolute left-[41px] top-8 bottom-8 w-0.5 bg-gradient-to-b from-primary/30 to-purple-200"></div>

                                    {/* Simple View of gathered details */}
                                    {reasoning.step_1_intent && (
                                        <div className="relative flex gap-5 mb-8 group">
                                            <div className="size-9 rounded-full bg-white border-2 border-primary/20 shadow-sm flex items-center justify-center z-10 text-primary shrink-0 transition-all">
                                                <span className="material-symbols-outlined text-[18px]">travel_explore</span>
                                            </div>
                                            <div className="flex-1 pt-0.5">
                                                <h4 className="text-xs font-bold text-text-secondary uppercase tracking-wider mb-1.5">Intenção Identificada</h4>
                                                <p className="text-sm text-text-main leading-relaxed bg-background/50 p-3 rounded-lg border border-border/50">{reasoning.step_1_intent}</p>
                                            </div>
                                        </div>
                                    )}

                                </div>
                            </div>
                        )}

                    </div>
                </div>
            </div>
        </div>
    );
};
