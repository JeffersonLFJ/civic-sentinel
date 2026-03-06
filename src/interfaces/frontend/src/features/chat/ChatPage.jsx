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

        // Get up to 6 recent messages for context (excluding the one we just added locally or AI placeholders)
        const recentHistory = messages
            .filter(m => !m.isAi || m.text.trim() !== '') // Filter empty AI placeholders
            .slice(-6) // Last 6 messages
            .map(m => ({
                role: m.isAi ? "assistant" : "user",
                content: m.text
            }));

        // Prepare the initial AI message placeholder
        const aiMsgId = Date.now() + 1;
        const initialAiMsg = {
            id: aiMsgId,
            sender: "Sentinela IA",
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            text: "",
            isAi: true,
            citations: []
        };
        setMessages(prev => [...prev, initialAiMsg]);

        try {
            const response = await fetch('/api/chat/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: userMsg.text,
                    user_id: userId,
                    history: recentHistory,
                    stream: true // Enabled SSE Streaming
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP Error: ${response.status}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder("utf-8");
            let firstChunkReceived = false;

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.trim() === '') continue;

                    try {
                        let data;
                        if (line.startsWith('data: ')) {
                            data = JSON.parse(line.substring(6));
                        } else {
                            data = JSON.parse(line);
                        }

                        if (data.type === 'citations' && data.data) {
                            if (!firstChunkReceived) {
                                setLoading(false);
                                firstChunkReceived = true;
                            }
                            // First frame usually has metadata
                            setMessages(prev => prev.map(msg =>
                                msg.id === aiMsgId ? { ...msg, citations: data.data } : msg
                            ));
                        }

                        if (data.type === 'token' && data.content) {
                            if (!firstChunkReceived) {
                                setLoading(false);
                                firstChunkReceived = true;
                            }
                            // Accumulate tokens
                            setMessages(prev => prev.map(msg =>
                                msg.id === aiMsgId ? { ...msg, text: msg.text + data.content } : msg
                            ));
                        }

                        if (data.type === 'done') {
                            // Stream complete
                            break;
                        }

                        // Also handle active listening responses (which come as standard JSON, not stream)
                        if (data.status === 'ambiguity_detected') {
                            if (!firstChunkReceived) { setLoading(false); firstChunkReceived = true; }
                            setMessages(prev => prev.map(msg =>
                                msg.id === aiMsgId ? { ...msg, text: data.response, isAmbiguous: true } : msg
                            ));
                        } else if (data.response && !data.type) {
                            if (!firstChunkReceived) { setLoading(false); firstChunkReceived = true; }
                            setMessages(prev => prev.map(msg =>
                                msg.id === aiMsgId ? { ...msg, text: data.response } : msg
                            ));
                        }
                    } catch (e) {
                        // Some lines might not be valid JSON if chunked mid-word, though rare with lines
                        console.warn("Error parsing chunk", line, e);
                    }
                }
            }

        } catch (error) {
            console.error("Chat Error:", error);
            setMessages(prev => {
                // Remove the empty placeholder if it failed completely
                const filtered = prev.filter(m => m.id !== aiMsgId || m.text !== "");
                return [...filtered, {
                    id: Date.now() + 2,
                    sender: "Sistema",
                    time: "",
                    text: "Erro ao comunicar com o servidor. Tente novamente.",
                    isAi: true
                }];
            });
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
                        <div className="flex flex-col gap-2 relative w-full">
                            <ChatMessage {...msg} />

                            {/* Active Listening Triggers */}
                            {msg.isAmbiguous && (
                                <div className="ml-14 max-w-xl mx-auto w-full flex flex-wrap gap-2 animate-fade-in mt-1">
                                    <button
                                        onClick={() => {
                                            setInput(msg.text.includes('refere a') ? msg.text.split('refere a ')[1].split(' ou')[0] : 'Sim');
                                            // Ideally this would trigger standard send, but simply setting input helps user
                                        }}
                                        className="text-xs bg-amber-50 text-amber-700 hover:bg-amber-100 px-3 py-1.5 rounded-full font-bold transition-colors border border-amber-200 flex items-center gap-1.5 shadow-sm"
                                    >
                                        <span className="material-symbols-outlined text-[14px]">check</span>
                                        Confirmar Intenção
                                    </button>
                                    <button
                                        onClick={() => {
                                            setInput("Na verdade me referia a: ");
                                        }}
                                        className="text-xs bg-white hover:bg-background-light px-3 py-1.5 rounded-full font-bold transition-colors border border-border/80 text-text-secondary flex items-center gap-1.5 shadow-sm"
                                    >
                                        <span className="material-symbols-outlined text-[14px]">edit</span>
                                        Reformular
                                    </button>
                                </div>
                            )}
                        </div>
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
