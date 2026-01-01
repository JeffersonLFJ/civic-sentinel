import React from 'react';

export const ConfirmationModal = ({
    isOpen,
    onClose,
    onConfirm,
    title = "Confirmar Ação",
    message = "Tem certeza que deseja prosseguir?",
    confirmText = "Confirmar",
    cancelText = "Cancelar",
    isDangerous = false
}) => {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-in fade-in duration-200">
            <div className="bg-surface border border-border rounded-xl shadow-2xl w-full max-w-sm overflow-hidden scale-100 transform transition-all">
                <div className="px-6 py-5 border-b border-border bg-background-light/30">
                    <h3 className="font-bold text-lg text-text-main leading-tight">{title}</h3>
                </div>

                <div className="p-6">
                    <p className="text-text-secondary text-sm leading-relaxed">{message}</p>
                </div>

                <div className="px-6 py-4 bg-background-light/50 border-t border-border flex justify-end gap-3">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 rounded-lg text-sm font-semibold text-text-secondary hover:bg-background border border-transparent hover:border-border transition-all"
                    >
                        {cancelText}
                    </button>
                    <button
                        onClick={() => { onConfirm(); onClose(); }}
                        className={`px-4 py-2 rounded-lg text-sm font-bold text-white shadow-lg transition-all transform active:scale-95 ${isDangerous
                                ? 'bg-red-500 hover:bg-red-600 shadow-red-500/20'
                                : 'bg-primary hover:bg-primary-hover shadow-primary/20'
                            }`}
                    >
                        {confirmText}
                    </button>
                </div>
            </div>
        </div>
    );
};
