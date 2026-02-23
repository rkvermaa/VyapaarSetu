"use client";

import { useState, useRef, useCallback } from "react";
import { Mic, MicOff } from "lucide-react";

interface VoiceInputProps {
  onTranscript: (text: string) => void;
  lang?: string;
}

export default function VoiceInput({ onTranscript, lang = "hi-IN" }: VoiceInputProps) {
  const [listening, setListening] = useState(false);
  const [supported, setSupported] = useState(true);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const recognitionRef = useRef<any>(null);
  const toggleListening = useCallback(() => {
    if (!("webkitSpeechRecognition" in window) && !("SpeechRecognition" in window)) { setSupported(false); return; }
    if (listening) { recognitionRef.current?.stop(); setListening(false); return; }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const w = window as any;
    const SR = w.SpeechRecognition || w.webkitSpeechRecognition;
    if (!SR) { setSupported(false); return; }
    const recognition = new SR();
    recognition.lang = lang;
    recognition.interimResults = false;
    recognition.continuous = false;
    recognition.onstart = () => setListening(true);
    recognition.onend = () => setListening(false);
    recognition.onerror = () => setListening(false);
    recognition.onresult = (ev: any) => { const t = ev.results[0]?.[0]?.transcript; if (t) onTranscript(t); };
    recognitionRef.current = recognition;
    recognition.start();
  }, [listening, lang, onTranscript]);
  if (!supported) return null;
  return (
    <button onClick={toggleListening} title={listening ? "Stop" : "Speak in Hindi/English"}
      className={"flex h-9 w-9 items-center justify-center rounded-lg transition-colors " +
        (listening ? "animate-pulse bg-red-500 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200")}
    >
      {listening ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
    </button>
  );
}
