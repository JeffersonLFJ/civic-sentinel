import React from 'react';
import { Link, useLocation } from 'react-router-dom';

const NavLink = ({ to, label, isActive }) => {
    const baseClasses = "px-5 py-2 rounded-full text-sm font-medium transition-all";
    const activeClasses = "bg-white text-primary shadow-sm border border-border/20 font-bold ring-1 ring-black/5";
    const inactiveClasses = "text-text-secondary hover:text-primary hover:bg-white";

    return (
        <Link to={to} className={`${baseClasses} ${isActive ? activeClasses : inactiveClasses}`}>
            {label}
        </Link>
    );
};

export const Header = () => {
    const location = useLocation();

    const navItems = [
        { label: "Chat", path: "/chat" },
        { label: "Documentos", path: "/documentos" },
        { label: "Quarentena", path: "/quarentena" },
        { label: "Inspetor de Dados", path: "/inspetor" },
        { label: "Auditoria", path: "/auditoria" },
        { label: "Cérebro", path: "/cerebro" },
    ];

    return (
        <header className="flex-none flex items-center justify-between whitespace-nowrap border-b border-border bg-surface/80 backdrop-blur-md px-8 py-4 z-30 relative shadow-sm">
            <div className="flex items-center gap-4">
                <div className="size-10 flex items-center justify-center text-primary bg-primary-soft rounded-xl shadow-sm transition-transform hover:scale-105">
                    <span className="material-symbols-outlined !text-[26px]">eco</span>
                </div>
                <div>
                    <h2 className="text-text-main text-lg font-bold leading-tight tracking-tight">Sentinela Cívico</h2>
                    <span className="text-text-secondary text-xs font-medium tracking-wide">Painel de Administração</span>
                </div>
            </div>

            <div className="flex flex-1 justify-end gap-8 items-center">
                <nav className="flex items-center gap-1 bg-background-light p-1.5 rounded-full border border-border/60 shadow-sm">
                    {navItems.map((item) => (
                        <NavLink
                            key={item.path}
                            to={item.path}
                            label={item.label}
                            isActive={location.pathname.startsWith(item.path)}
                        />
                    ))}
                </nav>

                <div className="flex items-center gap-3 border-l border-border pl-8">
                    <Link to="/chat" className="group relative flex items-center justify-center text-text-secondary hover:text-primary hover:bg-primary-soft transition-all rounded-full size-10" title="Voltar ao Chat">
                        <span className="material-symbols-outlined text-[24px]">chat</span>
                    </Link>
                    <button className="text-text-secondary hover:text-primary transition-colors rounded-full size-10 hover:bg-primary-soft flex items-center justify-center relative group">
                        <span className="material-symbols-outlined text-[24px]">notifications</span>
                        <span className="absolute top-2.5 right-2.5 size-2 bg-accent-orange rounded-full border border-surface"></span>
                    </button>
                </div>
            </div>
        </header>
    );
};
