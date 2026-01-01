import React, { useState } from 'react';
import { ChatMessage } from '../../components/ui/ChatMessage';

export const ChatPage = () => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [userId] = useState(() => `user-${Math.random().toString(36).substr(2, 9)}`); // Simple Session ID

    const sendMessage = async () => {
        if (!input.trim()) return;

        const userMsg = {
            id: Date.now(),
            sender: "Você",
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            text: input,
            isAi: false,
            align: 'right'
        };

        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setLoading(true);

        try {
            const response = await fetch('/api/chat/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: userMsg.text,
                    user_id: userId,
                    stream: false // For prototype simplicity, start with non-streaming to guarantee stability first
                })
            });

            const data = await response.json();

            const aiMsg = {
                id: Date.now() + 1,
                sender: "Sentinela IA",
                time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                text: data.response || "Sem resposta do servidor.",
                isAi: true
            };
            setMessages(prev => [...prev, aiMsg]);
        } catch (error) {
            console.error("Chat Error:", error);
            setMessages(prev => [...prev, {
                id: Date.now() + 1,
                sender: "Sistema",
                time: "",
                text: "Erro ao comunicar com o servidor.",
                isAi: true
            }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex-1 flex flex-col h-full bg-background-light/50 relative">
            <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-8 scroll-smooth" id="chat-container">
                <div className="flex justify-center py-4">
                    <div className="bg-surface text-text-muted text-[11px] font-medium px-4 py-1 rounded-full border border-border/50 uppercase tracking-widest shadow-sm">
                        Hoje, {new Date().toLocaleDateString()}
                    </div>
                </div>

                {messages.length === 0 && (
                    <div className="text-center text-text-muted mt-20">
                        <span className="material-symbols-outlined text-[48px] mb-4 opacity-20">chat_bubble</span>
                        <p>Inicie uma nova conversa com o Sentinela Cívico.</p>
                    </div>
                )}

                {messages.map(msg => (
                    <div key={msg.id} className={!msg.isAi ? "flex justify-end" : ""}>
                        <ChatMessage {...msg} />
                    </div>
                ))}

                {loading && (
                    <div className="flex items-start gap-3 max-w-4xl mx-auto w-full">
                        <div className="flex items-center gap-1 bg-white px-4 py-3 rounded-full rounded-tl-sm border border-border w-fit shadow-soft">
                            <div className="w-1.5 h-1.5 rounded-full bg-text-muted animate-bounce"></div>
                            <div className="w-1.5 h-1.5 rounded-full bg-text-muted animate-bounce [animation-delay:-.3s]"></div>
                            <div className="w-1.5 h-1.5 rounded-full bg-text-muted animate-bounce [animation-delay:-.5s]"></div>
                        </div>
                    </div>
                )}
            </div>

            {/* Input Area */}
            <div className="sticky bottom-0 bg-background-light/90 backdrop-blur-sm border-t border-border/50 p-4 md:p-6 z-20">
                <div className="max-w-4xl mx-auto w-full">
                    <div className="relative flex items-end gap-2 bg-surface p-2 rounded-3xl border border-border shadow-lg shadow-black/5 focus-within:ring-1 focus-within:ring-primary focus-within:border-primary transition-all">
                        <button className="p-2 text-text-muted hover:text-primary transition-colors rounded-full hover:bg-background h-10 w-10 flex items-center justify-center shrink-0">
                            <span className="material-symbols-outlined">attach_file</span>
                        </button>
                        <textarea
                            className="w-full bg-transparent border-none text-text-main placeholder-text-muted focus:ring-0 resize-none py-2 max-h-32 text-base leading-normal focus:outline-none"
                            placeholder="Digite sua dúvida sobre direitos, leis ou cidadania..."
                            rows="1"
                            style={{ minHeight: '40px' }}
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter' && !e.shiftKey) {
                                    e.preventDefault();
                                    sendMessage();
                                }
                            }}
                        ></textarea>
                        <button className="p-2 text-text-muted hover:text-primary transition-colors rounded-full hover:bg-background h-10 w-10 flex items-center justify-center shrink-0">
                            <span className="material-symbols-outlined">mic</span>
                        </button>
                        <button
                            onClick={sendMessage}
                            disabled={loading || !input.trim()}
                            className="p-2 bg-primary hover:bg-primary-hover text-white transition-all rounded-full h-10 w-10 flex items-center justify-center shadow-lg shadow-primary/30 shrink-0 disabled:opacity-50 disabled:cursor-not-allowed">
                            <span className="material-symbols-outlined text-[20px]">arrow_upward</span>
                        </button>
                    </div>
                    <div className="flex justify-between items-center px-4 mt-3">
                        <div className="flex flex-col gap-0.5 w-full text-center sm:text-left">
                            <p className="text-[11px] font-semibold text-text-secondary flex items-center gap-1.5 justify-center sm:justify-start">
                                <span className="material-symbols-outlined text-[14px]">visibility_off</span>
                                Chat anônimo e seguro.
                            </p>
                        </div>
                        <div className="hidden sm:flex items-center gap-1 text-[9px] text-text-muted uppercase font-bold tracking-widest shrink-0">
                            Sentinela Cívico v2.0
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
