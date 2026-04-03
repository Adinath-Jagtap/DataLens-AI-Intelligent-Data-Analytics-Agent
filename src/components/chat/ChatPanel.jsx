// src/components/chat/ChatPanel.jsx
import React, { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Loader2, Sparkles } from "lucide-react";
import { chatWithData } from "../../lib/groq";

const SUGGESTED = [
  "What are the key trends in this data?",
  "Which columns have the most missing values?",
  "What's the best chart to show correlations?",
  "Give me 3 business insights from this data.",
  "What anomalies do you see?",
];

function Message({ msg }) {
  const isAI = msg.role === "assistant";
  return (
    <div className={`flex gap-3 ${isAI ? "" : "flex-row-reverse"}`}>
      {/* Avatar */}
      <div className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5
        ${isAI ? "bg-surface-3" : "bg-accent-cyan/20"}`}>
        {isAI
          ? <Bot size={14} className="text-accent-violet" />
          : <User size={14} className="text-accent-cyan" />}
      </div>

      {/* Bubble */}
      <div className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm font-body leading-relaxed
        ${isAI
          ? "bg-surface-2 text-slate-200 rounded-tl-sm"
          : "bg-accent-cyan/10 text-slate-100 rounded-tr-sm border border-accent-cyan/20"}`}>
        {msg.streaming
          ? <span>{msg.content}<span className="inline-block w-1.5 h-4 bg-accent-cyan ml-0.5 animate-pulse rounded-sm" /></span>
          : msg.content
        }
      </div>
    </div>
  );
}

export default function ChatPanel({ datasetContext, chatHistory, onSave }) {
  const [messages, setMessages] = useState(
    chatHistory?.length > 0 ? chatHistory : [
      { role: "assistant", content: "Hi! I'm DataLens AI. Ask me anything about your dataset — trends, insights, anomalies, or what actions to take. 🔍" }
    ]
  );
  const [input,   setInput]   = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);
  const inputRef  = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (text) => {
    const content = text || input.trim();
    if (!content || loading) return;
    setInput("");

    const userMsg = { role: "user", content };
    const newMsgs = [...messages, userMsg];
    setMessages(newMsgs);
    setLoading(true);

    // Add streaming placeholder
    const aiPlaceholder = { role: "assistant", content: "", streaming: true };
    setMessages(m => [...m, aiPlaceholder]);

    try {
      const apiMessages = newMsgs
        .filter(m => !m.streaming)
        .map(m => ({ role: m.role, content: m.content }));

      let full = "";
      await chatWithData(apiMessages, datasetContext, (chunk, accumulated) => {
        full = accumulated;
        setMessages(m => {
          const updated = [...m];
          updated[updated.length - 1] = { role: "assistant", content: accumulated, streaming: true };
          return updated;
        });
      });

      const finalMsgs = [...newMsgs, { role: "assistant", content: full }];
      setMessages(finalMsgs);
      onSave?.(finalMsgs);
    } catch (err) {
      setMessages(m => {
        const updated = [...m];
        updated[updated.length - 1] = {
          role: "assistant",
          content: "Sorry, I couldn't get a response. Please check your Groq API key.",
        };
        return updated;
      });
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4 min-h-0">
        {messages.map((msg, i) => <Message key={i} msg={msg} />)}
        <div ref={bottomRef} />
      </div>

      {/* Suggestions (only when few messages) */}
      {messages.length <= 2 && (
        <div className="px-4 pb-3">
          <p className="text-xs text-slate-600 font-body mb-2 flex items-center gap-1">
            <Sparkles size={11} /> Try asking
          </p>
          <div className="flex flex-wrap gap-2">
            {SUGGESTED.map(s => (
              <button key={s} onClick={() => sendMessage(s)}
                      className="text-xs font-body px-3 py-1.5 rounded-full bg-surface-2 text-slate-400
                                 hover:bg-surface-3 hover:text-slate-200 transition-colors border border-surface-3">
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="px-4 pb-4 pt-2 border-t border-white/5">
        <div className="flex gap-2 items-end">
          <textarea
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Ask anything about your data…"
            rows={1}
            disabled={loading}
            className="input-field flex-1 resize-none min-h-[42px] max-h-32 py-2.5"
            style={{ lineHeight: "1.5" }}
          />
          <button onClick={() => sendMessage()} disabled={!input.trim() || loading}
                  className="btn-primary px-3 py-2.5 flex-shrink-0">
            {loading
              ? <Loader2 size={15} className="animate-spin" />
              : <Send size={15} />}
          </button>
        </div>
        <p className="text-xs text-slate-700 font-body mt-1.5">Enter to send · Shift+Enter for new line</p>
      </div>
    </div>
  );
}
