import React from 'react';

export const ProgressBar = ({ progress, label, colorClass = "bg-primary" }) => {
    return (
        <div className="w-full">
            <div className="flex justify-between mb-1">
                <span className="text-xs font-semibold text-text-main">{label}</span>
                <span className="text-xs font-mono text-text-muted">{Math.round(progress)}%</span>
            </div>
            <div className="w-full bg-background-light rounded-full h-2.5 overflow-hidden border border-border/50">
                <div
                    className={`h-2.5 rounded-full transition-all duration-500 ease-out ${colorClass}`}
                    style={{ width: `${Math.max(5, Math.min(100, progress))}%` }}
                >
                    <div className="w-full h-full opacity-30 bg-white/20 animate-pulse"></div>
                </div>
            </div>
        </div>
    );
};
