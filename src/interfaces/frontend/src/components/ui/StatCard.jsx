import React from 'react';

export const StatCard = ({ icon, label, value, colorClass }) => (
    <div className={`p-4 rounded-xl border border-border/50 bg-white/50 backdrop-blur-sm shadow-sm flex items-center gap-4 min-w-[180px] transition-all hover:scale-[1.02] hover:shadow-md`}>
        <div className={`size-10 rounded-lg flex items-center justify-center ${colorClass}`}>
            <span className="material-symbols-outlined text-[20px]">{icon}</span>
        </div>
        <div>
            <p className="text-[10px] uppercase tracking-wider font-bold text-text-muted mb-0.5">{label}</p>
            <p className="text-lg font-bold text-text-main font-mono">{value}</p>
        </div>
    </div>
);
