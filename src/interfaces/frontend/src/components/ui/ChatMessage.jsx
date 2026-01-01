import React from 'react';

export const ChatMessage = ({ sender, time, text, isAi, avatar, actions }) => (
    <div className={`flex items-start gap-4 max-w-4xl mx-auto w-full group/message ${!isAi && 'justify-end'}`}> {/* User messages aligned right? Mockup shows User on Left too in Auditoria, but Chat has User on Right? */}
        {/* Wait, let's check mockups.
      Auditoria: User (Maria) Left. AI (Sentinela) Left. All stacked.
      Chat (Step 30): 
      - User (Sentinela IA?? No, Sentinela IA is AI). Sentinela IA is Left. (Line 75)
      - User (Right Side? Line 90 `justify-end`). Yes.
      - Sentinela IA (Left).
      
      So Chat has Right/Left alignment. Auditoria has everything Left.
      
      I need to support `align` prop or deduce from `isAi`.
      If `isAi`, align Left. If User, align Right (for Chat) or Left (for Auditoria).
      
      Let's add `align` prop ('left' | 'right'). Default 'left'.
   */}

        {/* Left Avatar */}
        {avatar && <div className="flex-none size-9 rounded-full bg-cover bg-center shadow-sm border border-slate-100" style={{ backgroundImage: `url('${avatar}')` }}></div>}
        {isAi && !avatar && (
            <div className="flex-none size-9 rounded-full bg-gradient-to-br from-primary to-emerald-700 flex items-center justify-center text-white shadow-lg shadow-primary/20 ring-2 ring-white">
                <span className="material-symbols-outlined text-[18px]">smart_toy</span>
            </div>
        )}

        <div className={`flex flex-col gap-1.5 flex-1 min-w-0 ${!isAi ? 'items-end' : ''}`}>
            <div className={`flex items-baseline gap-2 ${!isAi ? 'mr-1' : 'ml-1'}`}>
                <span className={`text-xs font-bold ${isAi ? 'text-text-main' : 'text-text-secondary'}`}>{sender}</span>
                <span className="text-[10px] text-text-muted">{time}</span>
            </div>

            <div className={`p-5 rounded-3xl leading-relaxed max-w-[90%] md:max-w-[80%] shadow-soft text-base 
        ${isAi
                    ? 'bg-white text-text-main rounded-tl-sm border border-border/50'
                    : 'bg-primary text-white rounded-tr-sm shadow-md shadow-primary/10'}`}>
                {text}
            </div>

            {actions && (
                <div className="flex gap-2 mt-1 ml-1 opacity-0 group-hover/message:opacity-100 transition-opacity">
                    {actions}
                </div>
            )}
        </div>
    </div>
);
