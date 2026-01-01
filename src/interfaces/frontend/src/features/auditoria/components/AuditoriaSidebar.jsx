import React from 'react';

const InteractionCard = ({ id, time, name, role, avatar, message, status, latency, isActive }) => {
    return (
        <div className={`group cursor-pointer rounded-xl p-5 transition-all relative overflow-hidden border ${isActive ? 'bg-white border-primary shadow-soft' : 'bg-background hover:bg-white border-transparent hover:border-border hover:shadow-card'}`}>
            {isActive && <div className="absolute left-0 top-0 bottom-0 w-1.5 bg-primary"></div>}

            <div className={`flex justify-between items-start mb-3 ${isActive ? 'pl-2' : ''}`}>
                <div className="flex items-center gap-2">
                    <span className={`text-xs font-mono font-bold px-1.5 py-0.5 rounded ${isActive ? 'text-primary bg-primary-soft' : 'text-text-muted group-hover:text-text-secondary'}`}>
                        {id}
                    </span>
                </div>
                <span className="text-xs text-text-muted font-medium">{time}</span>
            </div>

            <div className={`flex items-center gap-3 mb-3 ${isActive ? 'pl-2' : ''}`}>
                {avatar ? (
                    <div className={`size-9 rounded-full bg-cover bg-center shadow-sm ${isActive ? 'ring-2 ring-primary-soft' : 'ring-2 ring-white'}`} style={{ backgroundImage: `url('${avatar}')` }}></div>
                ) : (
                    <div className="size-9 rounded-full bg-orange-100 flex items-center justify-center text-orange-600 font-bold text-xs ring-2 ring-white shadow-sm">
                        {name.charAt(0)}
                    </div>
                )}
                <div>
                    <p className="text-sm font-bold text-text-main leading-tight">{name}</p>
                    <p className="text-xs text-text-secondary mt-0.5">{role}</p>
                </div>
            </div>

            <p className={`text-sm text-text-secondary line-clamp-2 leading-relaxed mb-4 font-medium ${isActive ? 'pl-2' : ''}`}>
                "{message}"
            </p>

            <div className={`flex items-center justify-between border-t border-border/50 pt-3 ${isActive ? 'pl-2' : ''}`}>
                <div className="flex items-center gap-3">
                    <span className="flex items-center gap-1 text-[10px] text-text-muted font-medium bg-background px-2 py-1 rounded">
                        <span className="material-symbols-outlined text-[14px]">speed</span> {latency}
                    </span>
                </div>

                {status === 'verified' && (
                    <span className="flex items-center gap-1 text-[10px] text-primary font-bold bg-primary-soft px-2 py-1 rounded">
                        <span className="material-symbols-outlined text-[14px]">check_circle</span> Verificado
                    </span>
                )}
                {status === 'flagged' && (
                    <span className="flex items-center gap-1 text-[10px] text-accent-orange font-bold bg-orange-50 px-2 py-1 rounded">
                        <span className="material-symbols-outlined text-[14px]">warning</span> Sinalizado
                    </span>
                )}
                {status === 'reviewed' && (
                    <span className="flex items-center gap-1 text-[10px] text-primary font-bold bg-primary-soft px-2 py-1 rounded">
                        <span className="material-symbols-outlined text-[14px]">check_circle</span> Revisado
                    </span>
                )}
            </div>
        </div>
    );
};

export const AuditoriaSidebar = ({ onSelect, selectedId }) => {
    const [logs, setLogs] = React.useState([]);
    const [loading, setLoading] = React.useState(true);

    React.useEffect(() => {
        fetchLogs();
    }, []);

    const fetchLogs = async () => {
        try {
            const res = await fetch('/api/admin/stats');
            const data = await res.json();
            if (data.audit_logs) {
                setLogs(data.audit_logs);
            }
        } catch (error) {
            console.error("Failed to fetch audit logs", error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <aside className="w-[360px] flex-none flex flex-col bg-surface border-r border-border z-20 shadow-[4px_0_24px_-12px_rgba(0,0,0,0.05)]">
            <div className="p-6 pb-2 flex flex-col gap-5">
                <div className="flex items-center justify-between">
                    <h3 className="font-bold text-text-main text-lg tracking-tight">Interações Recentes</h3>
                    <span className="text-[10px] font-bold text-primary bg-primary-soft border border-primary/10 px-2.5 py-1 rounded-full">{logs.length} Total</span>
                </div>

                <div className="flex w-full items-center rounded-xl h-11 bg-background-light border border-border focus-within:border-primary focus-within:bg-white focus-within:ring-2 focus-within:ring-primary-soft transition-all shadow-sm">
                    <div className="text-text-muted flex items-center justify-center pl-4">
                        <span className="material-symbols-outlined text-[20px]">search</span>
                    </div>
                    <input className="flex w-full min-w-0 flex-1 bg-transparent border-none text-text-main focus:ring-0 placeholder:text-text-muted px-3 text-sm focus:outline-none" placeholder="Buscar ID, cidadão ou tema..." />
                </div>
            </div>

            <div className="flex-1 overflow-y-auto px-4 pb-4 space-y-3">
                {loading ? (
                    <div className="text-center py-10 text-text-muted">Carregando...</div>
                ) : logs.length === 0 ? (
                    <div className="text-center py-10 text-text-muted">Nenhuma interação registrada.</div>
                ) : (
                    logs.map(log => (
                        <div
                            key={log.id}
                            onClick={() => onSelect(log.id)}
                            className={`group cursor-pointer rounded-xl p-5 transition-all relative overflow-hidden border ${selectedId === log.id ? 'bg-white border-primary shadow-soft' : 'bg-background hover:bg-white border-transparent hover:border-border hover:shadow-card'}`}
                        >
                            {selectedId === log.id && <div className="absolute left-0 top-0 bottom-0 w-1.5 bg-primary"></div>}

                            <div className={`flex justify-between items-start mb-3 ${selectedId === log.id ? 'pl-2' : ''}`}>
                                <div className="flex items-center gap-2">
                                    <span className={`text-xs font-mono font-bold px-1.5 py-0.5 rounded ${selectedId === log.id ? 'text-primary bg-primary-soft' : 'text-text-muted group-hover:text-text-secondary'}`}>
                                        #{log.id.substring(0, 8).toUpperCase()}
                                    </span>
                                </div>
                                <span className="text-xs text-text-muted font-medium">{new Date(log.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                            </div>

                            <div className={`flex items-center gap-3 mb-3 ${selectedId === log.id ? 'pl-2' : ''}`}>
                                <div className="size-9 rounded-full bg-slate-100 flex items-center justify-center text-slate-500 font-bold text-xs ring-2 ring-white shadow-sm">
                                    A
                                </div>
                                <div>
                                    <p className="text-sm font-bold text-text-main leading-tight">Cidadão Anônimo</p>
                                    <p className="text-xs text-text-secondary mt-0.5">{log.action}</p>
                                </div>
                            </div>

                            <p className={`text-sm text-text-secondary line-clamp-2 leading-relaxed mb-4 font-medium ${selectedId === log.id ? 'pl-2' : ''}`}>
                                "{log.query || '(Sem texto)'}"
                            </p>

                            <div className={`flex items-center justify-between border-t border-border/50 pt-3 ${selectedId === log.id ? 'pl-2' : ''}`}>
                                {log.confidence_score && (
                                    <span className="flex items-center gap-1 text-[10px] text-text-muted font-medium bg-background px-2 py-1 rounded">
                                        <span className="material-symbols-outlined text-[14px]">psychology</span> {(log.confidence_score * 100).toFixed(0)}%
                                    </span>
                                )}
                            </div>
                        </div>
                    ))
                )}
            </div>
        </aside>
    );
};
