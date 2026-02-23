"use client";
import ChatPanel from "@/components/chat/ChatPanel";
import * as api from "@/lib/api";
import { BookOpen, HelpCircle } from "lucide-react";

const FAQS = [
  "What is ONDC?",
  "What is the TEAM scheme?",
  "What is an SNP?",
  "How long does ONDC onboarding take?",
  "What is Udyam registration?",
  "Which products can I sell on ONDC?",
  "What is CaaS (Cataloguing as a Service)?",
  "What are ONDC RET categories?",
];

export default function KnowledgePage() {
  return (
    <div className="h-screen flex flex-col">
      <div className="px-6 py-5 border-b border-gray-200 bg-white">
        <div className="flex items-center gap-2">
          <BookOpen className="h-5 w-5 text-indigo-700" />
          <h1 className="text-xl font-bold text-gray-900">Knowledge Base</h1>
        </div>
        <p className="text-sm text-gray-500 mt-1">Ask anything about ONDC, TEAM scheme, SNPs, or product cataloguing</p>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* FAQ shortcuts */}
        <div className="w-64 border-r border-gray-200 bg-white p-4 overflow-y-auto">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Quick Questions</p>
          <div className="space-y-2">
            {FAQS.map((q) => (
              <button
                key={q}
                className="w-full text-left rounded-lg px-3 py-2.5 text-sm text-gray-700 border border-gray-100 hover:bg-indigo-50 hover:border-indigo-200 hover:text-indigo-700 transition-colors"
              >
                <HelpCircle className="h-3.5 w-3.5 inline mr-1.5 text-gray-400" />
                {q}
              </button>
            ))}
          </div>
        </div>

        {/* Chat */}
        <div className="flex-1">
          <ChatPanel
            placeholder="Ask in Hindi or English — e.g. 'ONDC kya hai?' or 'SNP kaise select karein?'"
            initialMessage="Namaste! Main ONDC, TEAM scheme, aur product cataloguing ke baare mein aapke sawaalon ke jawab de sakta hoon. Kuch bhi poochhen!"
            onSendMessage={async (msg) => {
              const res = await api.sendMessage(msg);
              return res.response;
            }}
          />
        </div>
      </div>
    </div>
  );
}
