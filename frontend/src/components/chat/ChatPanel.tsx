"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Loader2 } from "lucide-react";
import VoiceInput from "@/components/voice/VoiceInput";

interface Message { role: "user" | "assistant"; content: string; }
interface ChatPanelProps {
  onSendMessage: (message: string) => Promise<string>;
  placeholder?: string;
  initialMessage?: string;
}

export default function ChatPanel({ onSendMessage, placeholder = "Describe your product...", initialMessage }: ChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>(
    initialMessage ? [{ role: "assistant", content: initialMessage }] : []
  );
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const sendMessage = async (text?: string) => {
    const msg = text || input.trim();
    if (!msg || loading) return;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: msg }]);
    setLoading(true);
    try {
      const response = await onSendMessage(msg);
      setMessages((prev) => [...prev, { role: "assistant", content: response }]);
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", content: "Sorry, something went wrong." }]);
    } finally { setLoading(false); }
  };

  return (
    <div className="flex h-full flex-col rounded-xl border border-gray-200 bg-white">
      <div className="flex items-center gap-2 border-b border-gray-200 px-4 py-3">
        <Bot className="h-5 w-5 text-indigo-800" />
        <span className="text-sm font-semibold text-gray-900">VyapaarSetu AI</span>
        <div className="ml-auto flex items-center gap-1 text-xs text-green-600">
          <div className="h-2 w-2 rounded-full bg-green-500" />Online
        </div>
      </div>
      <div className="flex-1 space-y-4 overflow-y-auto p-4">
        {messages.map((msg, i) => (
          <div key={i} className={"flex gap-3 " + (msg.role === "user" ? "flex-row-reverse" : "")}>
            <div className={"flex h-8 w-8 shrink-0 items-center justify-center rounded-full " +
              (msg.role === "user" ? "bg-indigo-800 text-white" : "bg-amber-100 text-amber-700")}>
              {msg.role === "user" ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
            </div>
            <div className={"max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed " +
              (msg.role === "user" ? "bg-indigo-800 text-white" : "bg-gray-100 text-gray-800")}>
              <p className="whitespace-pre-wrap">{msg.content}</p>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-amber-100 text-amber-700"><Bot className="h-4 w-4" /></div>
            <div className="flex items-center gap-2 rounded-2xl bg-gray-100 px-4 py-2.5">
              <Loader2 className="h-4 w-4 animate-spin text-gray-500" />
              <span className="text-sm text-gray-500">Thinking...</span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <div className="border-t border-gray-200 p-3">
        <div className="flex items-center gap-2">
          <VoiceInput onTranscript={(text) => sendMessage(text)} />
          <input type="text" value={input} onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            placeholder={placeholder} disabled={loading}
            className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none disabled:opacity-50" />
          <button onClick={() => sendMessage()} disabled={loading || !input.trim()}
            className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-800 text-white hover:bg-indigo-900 disabled:opacity-40">
            <Send className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
