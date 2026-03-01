"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";
import {
  Loader2, Bot, User, CheckCircle, AlertCircle,
  Clock, ChevronRight, Package, VolumeX, Volume2, Square,
} from "lucide-react";
import * as api from "@/lib/api";

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */
type Phase = "idle" | "user-speaking" | "processing" | "agent-speaking";
interface Message { role: "user" | "assistant"; content: string }

/* ------------------------------------------------------------------ */
/*  Constants — VAD thresholds                                         */
/* ------------------------------------------------------------------ */
const SPEAKING_THRESHOLD = 0.03;
const SILENCE_DURATION = 1500;   // stop after 1.5s silence
const MAX_RECORDING_MS = 15000;  // safety: auto-stop at 15s
const NO_SPEECH_TIMEOUT_MS = 5000; // nudge if silent 5s

/* ------------------------------------------------------------------ */
/*  Gradient Orb — ODRMitra style (220px, radial gradient, dual glow)  */
/* ------------------------------------------------------------------ */
function GradientOrb({ phase }: { phase: Phase }) {
  const colors: Record<Phase, { from: string; to: string; shadow: string }> = {
    idle:            { from: "#f97316", to: "#fbbf24", shadow: "rgba(249,115,22,0.25)" },
    "user-speaking": { from: "#3b82f6", to: "#60a5fa", shadow: "rgba(59,130,246,0.35)" },
    processing:      { from: "#f59e0b", to: "#f97316", shadow: "rgba(245,158,11,0.3)" },
    "agent-speaking":{ from: "#f97316", to: "#ef4444", shadow: "rgba(249,115,22,0.35)" },
  };
  const c = colors[phase];
  const isActive = phase !== "idle";

  return (
    <div className="relative flex items-center justify-center" style={{ width: 280, height: 280 }}>
      {isActive && (
        <>
          <div className="absolute rounded-full animate-ping"
            style={{ width: 280, height: 280, background: `radial-gradient(circle, ${c.shadow}, transparent 70%)`, animationDuration: "2s" }} />
          <div className="absolute rounded-full animate-pulse"
            style={{ width: 260, height: 260, background: `radial-gradient(circle, ${c.shadow}, transparent 60%)`, animationDuration: "1.5s" }} />
        </>
      )}
      <div className="relative rounded-full transition-all duration-700"
        style={{
          width: 220, height: 220,
          background: `radial-gradient(circle at 35% 35%, ${c.from}40, ${c.to}80, ${c.from}30)`,
          boxShadow: `0 0 80px ${c.shadow}, 0 0 120px ${c.shadow}`,
          transform: isActive ? "scale(1.05)" : "scale(1)",
        }}>
        <div className="absolute rounded-full"
          style={{ top: "15%", left: "20%", width: "40%", height: "40%",
            background: "radial-gradient(circle, rgba(255,255,255,0.3), transparent)", filter: "blur(10px)" }} />
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Phase Label                                                        */
/* ------------------------------------------------------------------ */
function PhaseLabel({ phase, active }: { phase: Phase; active: boolean }) {
  const labels: Record<Phase, string> = {
    idle: active ? "Ready..." : "Click to start",
    "user-speaking": "Listening...",
    processing: "Processing...",
    "agent-speaking": "Speaking...",
  };
  const colors: Record<Phase, string> = {
    idle: "text-gray-500", "user-speaking": "text-blue-600",
    processing: "text-amber-600", "agent-speaking": "text-orange-600",
  };
  return <p className={`text-sm font-medium ${colors[phase]} mt-4 transition-colors`}>{labels[phase]}</p>;
}

/* ------------------------------------------------------------------ */
/*  Helpers                                                             */
/* ------------------------------------------------------------------ */
function ComplianceBadge({ score }: { score: number | null }) {
  if (score === null) return <span className="text-xs text-gray-400">Pending</span>;
  const color = score >= 80 ? "text-green-600 bg-green-50" : score >= 50 ? "text-amber-600 bg-amber-50" : "text-red-600 bg-red-50";
  return <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${color}`}>{score.toFixed(0)}%</span>;
}
function StatusIcon({ status }: { status: string }) {
  if (status === "ready") return <CheckCircle className="h-4 w-4 text-green-500" />;
  if (status === "draft") return <Clock className="h-4 w-4 text-amber-500" />;
  return <AlertCircle className="h-4 w-4 text-red-500" />;
}

const FIELD_LABELS: Record<string, string> = {
  mobile_verified: "Mobile Number",
  product_name: "Product Name",
  mrp: "MRP (₹)",
  material: "Material",
  moq: "MOQ",
  hsn_code: "HSN Code",
  country_of_origin: "Country of Origin",
};

/** Strip [FIELDS]{...}[/FIELDS], [PRODUCT_DONE], [CATALOGUE_COMPLETE] from response text. */
function parseResponse(raw: string): {
  text: string;
  fields: Record<string, string> | null;
  productDone: boolean;
  catalogueComplete: boolean;
} {
  const match = raw.match(/\[FIELDS\]([\s\S]*?)\[\/FIELDS\]/);
  let text = raw
    .replace(/\[FIELDS\][\s\S]*?\[\/FIELDS\]/, "")
    .replace(/\[PRODUCT_DONE\]/g, "")
    .replace(/\[CATALOGUE_COMPLETE\]/g, "")
    .trim();
  let fields: Record<string, string> | null = null;
  if (match) {
    try { fields = JSON.parse(match[1]); } catch { /* ignore */ }
  }
  const productDone = raw.includes("[PRODUCT_DONE]");
  const catalogueComplete = raw.includes("[CATALOGUE_COMPLETE]");
  return { text, fields, productDone, catalogueComplete };
}

/** Build a raw description string from extracted voice fields for POST /products/. */
function buildRawDescription(fields: Record<string, string>): string {
  // Build from all fields except mobile_verified
  const parts: string[] = [];
  for (const [key, value] of Object.entries(fields)) {
    if (key === "mobile_verified" || !value) continue;
    if (key === "hsn_code" && value.toLowerCase() === "nahi") continue;
    parts.push(`${key}: ${value}`);
  }
  return parts.join(", ");
}

/* ================================================================== */
/*  MAIN PAGE                                                          */
/* ================================================================== */
export default function CataloguePage() {
  const router = useRouter();

  /* ---- State ---- */
  const [phase, setPhase] = useState<Phase>("idle");
  const [conversationActive, setConversationActive] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [products, setProducts] = useState<api.Product[]>([]);
  const [catalogueStatus, setCatalogueStatus] = useState<{
    total_products: number; ready_products: number; avg_compliance_score: number; catalogue_ready: boolean;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [extractedFields, setExtractedFields] = useState<Record<string, string>>({});
  const [muted, setMuted] = useState(false);
  const [mseProfile, setMseProfile] = useState<api.MSEProfile | null>(null);

  /* ---- Refs ---- */
  const transcriptEndRef = useRef<HTMLDivElement>(null);
  const conversationActiveRef = useRef(false);
  const mutedRef = useRef(false);
  const stoppingRef = useRef(false);
  const isRecordingRef = useRef(false);
  const hasSpokenRef = useRef(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const scriptNodeRef = useRef<ScriptProcessorNode | null>(null);
  const silenceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const maxRecordTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const noSpeechTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const responseAudioRef = useRef<HTMLAudioElement | null>(null);
  const messagesRef = useRef<Message[]>([]);
  const pendingAssistantMsgRef = useRef<string | null>(null);
  const startRecordingRef = useRef<(() => void) | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const isFirstMessageRef = useRef(true);
  const catalogueCompleteRef = useRef(false);
  const extractedFieldsRef = useRef<Record<string, string>>({});

  useEffect(() => { conversationActiveRef.current = conversationActive; }, [conversationActive]);
  useEffect(() => { mutedRef.current = muted; }, [muted]);
  useEffect(() => { messagesRef.current = messages; }, [messages]);
  useEffect(() => { extractedFieldsRef.current = extractedFields; }, [extractedFields]);
  useEffect(() => { transcriptEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, phase]);

  // Persistent Audio element — auto-restart recording when TTS ends (ODRMitra pattern)
  useEffect(() => {
    responseAudioRef.current = new Audio();
    responseAudioRef.current.onended = () => {
      if (catalogueCompleteRef.current) {
        // Catalogue complete — auto-stop conversation after farewell finishes
        catalogueCompleteRef.current = false;
        conversationActiveRef.current = false;
        setConversationActive(false);
        setPhase("idle");
        toast.success("Products saved! Catalogue ready.");
        loadProducts();
        return;
      }
      if (conversationActiveRef.current && !stoppingRef.current) {
        startRecordingRef.current?.();
      } else {
        setPhase("idle");
      }
    };
    responseAudioRef.current.onerror = () => {
      if (catalogueCompleteRef.current) {
        catalogueCompleteRef.current = false;
        conversationActiveRef.current = false;
        setConversationActive(false);
        setPhase("idle");
        toast.success("Products saved! Catalogue ready.");
        loadProducts();
        return;
      }
      if (conversationActiveRef.current && !stoppingRef.current) {
        startRecordingRef.current?.();
      } else {
        setPhase("idle");
      }
    };
    return () => {
      responseAudioRef.current?.pause();
      streamRef.current?.getTracks().forEach(t => t.stop());
      audioContextRef.current?.close();
    };
  }, []);

  /* ---- Load products (does NOT touch extractedFields — those are voice-only) ---- */
  const loadProducts = useCallback(async () => {
    try {
      const [prods, status] = await Promise.all([api.listProducts(), api.getCatalogueStatus()]);
      setProducts(prods);
      setCatalogueStatus(status);
    } catch { /* silent */ }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { loadProducts(); }, [loadProducts]);
  useEffect(() => { api.getMSEProfile().then(setMseProfile).catch(() => {}); }, []);

  /* ---- Cleanup recording resources ---- */
  const cleanupRecording = useCallback(() => {
    if (silenceTimerRef.current) { clearTimeout(silenceTimerRef.current); silenceTimerRef.current = null; }
    if (maxRecordTimerRef.current) { clearTimeout(maxRecordTimerRef.current); maxRecordTimerRef.current = null; }
    if (noSpeechTimerRef.current) { clearTimeout(noSpeechTimerRef.current); noSpeechTimerRef.current = null; }
    if (scriptNodeRef.current) { try { scriptNodeRef.current.disconnect(); } catch { /* */ } scriptNodeRef.current = null; }
    if (analyserRef.current) { try { analyserRef.current.disconnect(); } catch { /* */ } analyserRef.current = null; }
    if (audioContextRef.current) { try { audioContextRef.current.close(); } catch { /* */ } audioContextRef.current = null; }
    if (streamRef.current) { streamRef.current.getTracks().forEach(t => t.stop()); streamRef.current = null; }
  }, []);

  /* ---- Play TTS via Sarvam (ODRMitra pattern: show text when audio starts) ---- */
  const playTTS = useCallback(async (text: string, langCode = "hi-IN"): Promise<void> => {
    if (mutedRef.current || !text) {
      // Muted — show text immediately, skip audio
      if (pendingAssistantMsgRef.current) {
        const msg = pendingAssistantMsgRef.current;
        pendingAssistantMsgRef.current = null;
        setMessages(prev => [...prev, { role: "assistant", content: msg }]);
      }
      return;
    }
    try {
      const { audio_id } = await api.voiceTTS(text, langCode);
      const audio = responseAudioRef.current;
      if (audio_id && audio) {
        setPhase("agent-speaking");

        // Show the text bubble only when audio actually starts playing
        const flushPendingMsg = () => {
          if (pendingAssistantMsgRef.current) {
            const msg = pendingAssistantMsgRef.current;
            pendingAssistantMsgRef.current = null;
            setMessages(prev => [...prev, { role: "assistant", content: msg }]);
          }
          audio.removeEventListener("playing", flushPendingMsg);
        };
        audio.addEventListener("playing", flushPendingMsg);

        // Set audio source — persistent element, no new Audio() each time
        audio.src = api.voiceAudioURL(audio_id);
        audio.play().catch(() => {
          // Play failed — show text anyway
          flushPendingMsg();
        });
      } else {
        // No audio — show text immediately
        if (pendingAssistantMsgRef.current) {
          const msg = pendingAssistantMsgRef.current;
          pendingAssistantMsgRef.current = null;
          setMessages(prev => [...prev, { role: "assistant", content: msg }]);
        }
        setPhase("idle");
      }
    } catch {
      // TTS failed — show text immediately
      if (pendingAssistantMsgRef.current) {
        const msg = pendingAssistantMsgRef.current;
        pendingAssistantMsgRef.current = null;
        setMessages(prev => [...prev, { role: "assistant", content: msg }]);
      }
    }
  }, []);

  /* ---- Process pipeline: STT → LLM → LID → TTS ---- */
  const processPipeline = useCallback(async (audioBlob: Blob) => {
    if (!conversationActiveRef.current) { setPhase("idle"); return; }
    setPhase("processing");

    try {
      // 1. STT
      const { transcript } = await api.voiceSTT(audioBlob);
      if (!conversationActiveRef.current) { setPhase("idle"); return; }
      if (!transcript.trim()) {
        if (conversationActiveRef.current) startRecordingRef.current?.();
        else setPhase("idle");
        return;
      }

      setMessages(prev => [...prev, { role: "user", content: transcript }]);

      // 2. LID → detect language for TTS
      const langCode = await api.voiceLID(transcript).then(r => r.language_code || "hi-IN").catch(() => "hi-IN");

      if (!conversationActiveRef.current) { setPhase("idle"); return; }

      // 3. LLM (catalogue chat) — first message forces new session
      const forceNew = isFirstMessageRef.current;
      isFirstMessageRef.current = false;
      const res = await api.catalogueChat(transcript, "voice", forceNew);
      if (!conversationActiveRef.current) { setPhase("idle"); return; }

      const { text: response, fields, productDone, catalogueComplete } = parseResponse(res.response);

      // Update extracted fields from [FIELDS] tags
      if (fields) {
        setExtractedFields(prev => ({ ...prev, ...fields }));
        extractedFieldsRef.current = { ...extractedFieldsRef.current, ...fields };
      }

      // Handle [PRODUCT_DONE] — save current product in background
      if (productDone) {
        const currentFields = { ...extractedFieldsRef.current };
        const rawDesc = buildRawDescription(currentFields);
        console.log("[PRODUCT_DONE] fields:", currentFields, "rawDesc:", rawDesc);
        if (rawDesc) {
          api.addProduct(rawDesc, "voice", currentFields).then(() => {
            loadProducts();
            toast.success("Product saved!");
          }).catch((err) => {
            console.error("Product save failed:", err);
            toast.error("Product save failed");
          });
        } else {
          console.warn("[PRODUCT_DONE] but rawDesc is empty — fields were:", currentFields);
          toast.error("No product data to save");
        }
        // Reset fields to only mobile_verified for next product
        const mobileOnly: Record<string, string> = {};
        if (currentFields.mobile_verified) mobileOnly.mobile_verified = currentFields.mobile_verified;
        setExtractedFields(mobileOnly);
        extractedFieldsRef.current = mobileOnly;
      }

      // Handle [CATALOGUE_COMPLETE] — save final product + auto-disconnect after TTS
      if (catalogueComplete) {
        const currentFields = { ...extractedFieldsRef.current };
        const rawDesc = buildRawDescription(currentFields);
        console.log("[CATALOGUE_COMPLETE] fields:", currentFields, "rawDesc:", rawDesc);
        if (rawDesc && Object.keys(currentFields).some(k => k !== "mobile_verified")) {
          api.addProduct(rawDesc, "voice", currentFields).then(() => loadProducts()).catch((err) => {
            console.error("Final product save failed:", err);
          });
        }
        catalogueCompleteRef.current = true;
      }

      // 4. Store as pending — text will appear when TTS starts playing
      pendingAssistantMsgRef.current = response;

      // Force hi-IN for Hindi/Hinglish content
      let ttsLang = langCode;
      if (ttsLang === "en-IN" && /[ा-ो]|achha|kya|hai|karna|bata|nahi|haan/i.test(response)) {
        ttsLang = "hi-IN";
      }

      // 5. TTS → speak response (text shown when audio starts, auto-record on end)
      await playTTS(response, ttsLang);

      // Reload products in background (only if not already triggered above)
      if (!productDone && !catalogueComplete) loadProducts();

    } catch {
      if (conversationActiveRef.current) {
        setMessages(prev => [...prev, { role: "assistant", content: "Kuch problem aa gayi. Dobara boliye." }]);
      }
      setPhase("idle");
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [playTTS, loadProducts]);

  /* ---- Stop recording ---- */
  const stopRecording = useCallback(() => {
    if (!isRecordingRef.current) return;
    isRecordingRef.current = false;
    if (mediaRecorderRef.current?.state === "recording") {
      try { mediaRecorderRef.current.stop(); } catch { /* */ }
    }
  }, []);

  /* ---- Start recording with VAD ---- */
  const startRecording = useCallback(async () => {
    if (isRecordingRef.current || !conversationActiveRef.current) return;

    // Pause any playing TTS
    if (responseAudioRef.current) {
      responseAudioRef.current.pause();
      responseAudioRef.current.currentTime = 0;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true },
      });
      streamRef.current = stream;

      const ctx = new AudioContext();
      audioContextRef.current = ctx;
      const source = ctx.createMediaStreamSource(stream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 256;
      analyser.smoothingTimeConstant = 0.7;
      source.connect(analyser);
      analyserRef.current = analyser;

      // VAD via ScriptProcessor
      const scriptNode = ctx.createScriptProcessor(2048, 1, 1);
      analyser.connect(scriptNode);
      scriptNodeRef.current = scriptNode;
      hasSpokenRef.current = false;

      scriptNode.onaudioprocess = () => {
        if (!isRecordingRef.current) return;
        const vadData = new Uint8Array(analyser.fftSize);
        analyser.getByteTimeDomainData(vadData);
        let sum = 0;
        for (let i = 0; i < vadData.length; i++) {
          const n = vadData[i] / 128.0 - 1.0;
          sum += n * n;
        }
        const rms = Math.sqrt(sum / vadData.length);

        if (rms > SPEAKING_THRESHOLD) {
          hasSpokenRef.current = true;
          if (noSpeechTimerRef.current) { clearTimeout(noSpeechTimerRef.current); noSpeechTimerRef.current = null; }
          if (silenceTimerRef.current) { clearTimeout(silenceTimerRef.current); silenceTimerRef.current = null; }
        } else if (hasSpokenRef.current && !silenceTimerRef.current) {
          silenceTimerRef.current = setTimeout(() => stopRecording(), SILENCE_DURATION);
        }
      };
      scriptNode.connect(ctx.destination);

      // MediaRecorder
      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;
      audioChunksRef.current = [];

      recorder.ondataavailable = (e) => audioChunksRef.current.push(e.data);
      recorder.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: "audio/wav" });
        audioChunksRef.current = [];
        cleanupRecording();

        if (stoppingRef.current || !conversationActiveRef.current) {
          stoppingRef.current = false;
          setPhase("idle");
          return;
        }
        if (blob.size > 0) {
          processPipeline(blob);
        } else {
          setPhase("idle");
        }
      };

      recorder.start();
      isRecordingRef.current = true;
      setPhase("user-speaking");

      // Safety: auto-stop at 15s
      maxRecordTimerRef.current = setTimeout(() => {
        if (isRecordingRef.current) stopRecording();
      }, MAX_RECORDING_MS);

      // No-speech nudge after 5s
      noSpeechTimerRef.current = setTimeout(async () => {
        if (isRecordingRef.current && !hasSpokenRef.current) {
          stoppingRef.current = true;
          if (mediaRecorderRef.current?.state === "recording") {
            try { mediaRecorderRef.current.stop(); } catch { /* */ }
          }
          isRecordingRef.current = false;
          cleanupRecording();
          stoppingRef.current = false;

          if (!conversationActiveRef.current) { setPhase("idle"); return; }

          const lastMsg = [...messagesRef.current].reverse().find(m => m.role === "assistant");
          const nudge = lastMsg
            ? `Ji, mujhe sunai nahi diya. ${lastMsg.content}`
            : "Ji, mujhe kuch sunai nahi diya. Kya aap dobara bol sakte hain?";

          setMessages(prev => [...prev, { role: "assistant", content: nudge }]);
          setPhase("agent-speaking");
          await playTTS(nudge, "hi-IN");

          if (conversationActiveRef.current) {
            setPhase("idle");
            setTimeout(() => { if (conversationActiveRef.current) startRecordingRef.current?.(); }, 500);
          }
        }
      }, NO_SPEECH_TIMEOUT_MS);

    } catch {
      toast.error("Microphone access denied");
      setPhase("idle");
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [processPipeline, stopRecording, cleanupRecording, playTTS]);

  // Store startRecording in ref so persistent Audio onended can call it
  useEffect(() => { startRecordingRef.current = startRecording; }, [startRecording]);

  /* ---- Start conversation ---- */
  const startConversation = useCallback(async () => {
    setConversationActive(true);
    conversationActiveRef.current = true;
    isFirstMessageRef.current = true;
    catalogueCompleteRef.current = false;

    // Clear previous conversation state
    setExtractedFields({});
    extractedFieldsRef.current = {};
    setMessages([]);

    const name = mseProfile?.owner_name;
    const greeting = name
      ? `Namaste ${name} ji! VyapaarSetu mein aapka swagat hai. Verification ke liye aapka registered mobile number bata dijiye.`
      : "Namaste! VyapaarSetu mein aapka swagat hai. Verification ke liye aapka mobile number bata dijiye.";

    // Store as pending — text appears when audio starts playing
    pendingAssistantMsgRef.current = greeting;

    // Play greeting — text shows when audio starts, auto-record on end
    await playTTS(greeting, "hi-IN");
  }, [playTTS, mseProfile]);

  /* ---- Stop conversation ---- */
  const stopConversation = useCallback(() => {
    // Mark inactive FIRST so all async loops see it immediately
    conversationActiveRef.current = false;
    setConversationActive(false);
    stoppingRef.current = true;

    // Stop recording
    if (isRecordingRef.current && mediaRecorderRef.current?.state === "recording") {
      try { mediaRecorderRef.current.stop(); } catch { /* */ }
    }
    isRecordingRef.current = false;
    cleanupRecording();

    // Stop audio playback (don't null — persistent element reused next conversation)
    if (responseAudioRef.current) {
      responseAudioRef.current.pause();
      responseAudioRef.current.currentTime = 0;
    }

    // Abort any in-flight fetch requests
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }

    setPhase("idle");

    // Reset stopping flag after a tick so onstop handler sees it
    setTimeout(() => { stoppingRef.current = false; }, 200);
  }, [cleanupRecording]);

  /* ---- Orb click ---- */
  const handleOrbClick = useCallback(() => {
    if (!conversationActive) { startConversation(); return; }
    if (phase === "idle") startRecordingRef.current?.();
    else if (phase === "user-speaking") stopRecording();
    else if (phase === "agent-speaking") {
      if (responseAudioRef.current) { responseAudioRef.current.pause(); }
      setPhase("idle");
    }
  }, [conversationActive, phase, startConversation, stopRecording]);

  /* ---- Mute ---- */
  const toggleMute = useCallback(() => {
    const next = !muted;
    setMuted(next);
    if (next && responseAudioRef.current) { responseAudioRef.current.pause(); responseAudioRef.current.currentTime = 0; }
  }, [muted]);

  const filledCount = Object.keys(extractedFields).length;
  const totalFields = Object.keys(FIELD_LABELS).length;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full py-20">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col">
      {/* Progress */}
      <div className="px-6 pt-6 pb-3 border-b border-gray-200 bg-white">
        <div className="flex items-center gap-2 mb-2">
          {["Profile", "Catalogue", "SNP Match"].map((step, i) => (
            <div key={step} className="flex items-center gap-2">
              <div className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold
                ${i === 1 ? "bg-indigo-800 text-white" : i < 1 ? "bg-green-500 text-white" : "bg-gray-200 text-gray-500"}`}>
                {i < 1 ? "✓" : i + 1}
              </div>
              <span className={`text-sm ${i === 1 ? "text-indigo-800 font-medium" : "text-gray-400"}`}>{step}</span>
              {i < 2 && <div className="w-8 h-0.5 bg-gray-200" />}
            </div>
          ))}
        </div>
        {catalogueStatus && (
          <div className="flex items-center gap-4 text-sm">
            <span className="text-gray-500">{catalogueStatus.total_products} products</span>
            <span className="text-green-600 font-medium">{catalogueStatus.ready_products} ready</span>
            {catalogueStatus.avg_compliance_score > 0 && (
              <span className="text-amber-600">Avg compliance: {catalogueStatus.avg_compliance_score.toFixed(0)}%</span>
            )}
            {catalogueStatus.catalogue_ready && (
              <button onClick={() => router.push("/onboarding/match")}
                className="ml-auto flex items-center gap-1 rounded-lg bg-green-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-green-700">
                Next: Find SNP <ChevronRight className="h-4 w-4" />
              </button>
            )}
          </div>
        )}
      </div>

      {/* Main */}
      <div className="flex flex-1 overflow-hidden">
        {/* ============ LEFT ============ */}
        <div className="flex-1 flex flex-col bg-gradient-to-b from-gray-50 to-white">
          {!conversationActive ? (
            <div className="flex-1 flex flex-col items-center justify-center px-8">
              <div className="text-center max-w-md">
                <h2 className="text-2xl font-bold text-gray-900 mb-2">AI Catalogue Builder</h2>
                <p className="text-gray-500 mb-1">Apne products ke baare mein Hindi ya English mein bataiye</p>
                <p className="text-sm text-gray-400 mb-8">AI will classify to ONDC category and extract attributes</p>
                <div className="flex justify-center">
                  <GradientOrb phase="idle" />
                </div>
                <p className="text-sm text-gray-500 mt-6 mb-4">Start a voice conversation to add products</p>
                <button onClick={startConversation}
                  className="rounded-xl bg-gray-900 px-8 py-3 text-sm font-semibold text-white hover:bg-black shadow-lg hover:shadow-xl transition-all">
                  Start Speaking
                </button>
                {products.length > 0 && (
                  <p className="mt-4 text-xs text-gray-400">You have {products.length} product(s). Start to add more.</p>
                )}
              </div>
            </div>
          ) : (
            <>
              {/* Orb */}
              <div className="flex flex-col items-center pt-8 pb-4">
                <div className="flex justify-center cursor-pointer" onClick={handleOrbClick}>
                  <GradientOrb phase={phase} />
                </div>
                <PhaseLabel phase={phase} active={conversationActive} />
                <div className="flex items-center gap-3 mt-4">
                  <button onClick={toggleMute} title={muted ? "Unmute" : "Mute"}
                    className={`flex h-9 w-9 items-center justify-center rounded-full transition-colors
                      ${muted ? "bg-red-100 text-red-600" : "bg-gray-100 text-gray-500 hover:bg-gray-200"}`}>
                    {muted ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
                  </button>
                  <button onClick={stopConversation}
                    className="flex items-center gap-1.5 rounded-full bg-gray-900 px-5 py-2 text-xs font-medium text-white hover:bg-black transition-colors">
                    <Square className="h-3 w-3" /> Stop Conversation
                  </button>
                </div>
              </div>

              {/* Transcript */}
              <div className="flex-1 overflow-y-auto border-t border-gray-100 px-6 py-4">
                <div className="max-w-lg mx-auto space-y-3">
                  {messages.map((msg, i) => (
                    <div key={i}
                      className={`flex gap-2.5 ${msg.role === "user" ? "flex-row-reverse" : ""}`}
                      style={{ animation: "fadeSlideUp 0.3s ease-out" }}>
                      <div className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full
                        ${msg.role === "user" ? "bg-blue-600 text-white" : "bg-amber-100 text-amber-700"}`}>
                        {msg.role === "user" ? <User className="h-3.5 w-3.5" /> : <Bot className="h-3.5 w-3.5" />}
                      </div>
                      <div className={`max-w-[80%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed
                        ${msg.role === "user" ? "bg-blue-600 text-white" : "bg-gray-50 text-gray-800 border border-gray-100"}`}>
                        <p className="whitespace-pre-wrap">{msg.content}</p>
                      </div>
                    </div>
                  ))}
                  {phase === "processing" && (
                    <div className="flex gap-2.5" style={{ animation: "fadeSlideUp 0.3s ease-out" }}>
                      <div className="flex h-7 w-7 items-center justify-center rounded-full bg-amber-100 text-amber-700">
                        <Bot className="h-3.5 w-3.5" />
                      </div>
                      <div className="rounded-2xl bg-amber-50 border border-amber-100 px-3.5 py-2.5">
                        <div className="flex items-center gap-2">
                          <Loader2 className="h-3.5 w-3.5 animate-spin text-amber-500" />
                          <span className="text-xs text-amber-600">Thinking...</span>
                        </div>
                      </div>
                    </div>
                  )}
                  <div ref={transcriptEndRef} />
                </div>
              </div>
            </>
          )}
        </div>

        {/* ============ RIGHT ============ */}
        <div className="w-80 border-l border-gray-200 bg-white flex flex-col overflow-hidden">
          <div className="p-5 border-b border-gray-100">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-gray-900">Product Fields</h3>
              <span className="text-xs text-gray-400">{filledCount}/{totalFields}</span>
            </div>
            <div className="h-2 rounded-full bg-gray-100 mb-4">
              <div className="h-2 rounded-full bg-indigo-600 transition-all duration-500"
                style={{ width: `${totalFields > 0 ? (filledCount / totalFields) * 100 : 0}%` }} />
            </div>
            <div className="space-y-2">
              {Object.entries(FIELD_LABELS).map(([key, label]) => {
                const value = extractedFields[key];
                return (
                  <div key={key} className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition-all
                    ${value ? "bg-green-50 border border-green-100" : "bg-gray-50 border border-gray-100"}`}>
                    {value
                      ? <CheckCircle className="h-4 w-4 text-green-500 shrink-0" />
                      : <div className="h-4 w-4 rounded-full border-2 border-gray-300 shrink-0" />}
                    <div className="flex-1 min-w-0">
                      <span className={`text-xs ${value ? "text-green-700 font-medium" : "text-gray-400"}`}>{label}</span>
                      {value && <p className="text-xs text-green-900 font-semibold truncate">{value}</p>}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="flex-1 overflow-y-auto">
            <div className="p-4">
              <h3 className="text-sm font-semibold text-gray-900 mb-3">My Products ({products.length})</h3>
              {products.length === 0 ? (
                <div className="text-center py-6 text-gray-400">
                  <Package className="h-10 w-10 mx-auto mb-2 text-gray-200" />
                  <p className="text-xs">No products yet</p>
                  <p className="text-xs mt-1">Start the AI assistant to add products</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {products.map(p => (
                    <div key={p.id} className="rounded-lg border border-gray-100 p-3 hover:bg-gray-50 transition-colors">
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-800 truncate">{p.product_name || "Unnamed"}</p>
                          <p className="text-xs text-gray-400 mt-0.5 truncate">{p.ondc_category_code || "Classifying..."}</p>
                        </div>
                        <div className="flex items-center gap-1 shrink-0">
                          <StatusIcon status={p.status} />
                          <ComplianceBadge score={p.compliance_score} />
                        </div>
                      </div>
                      {p.missing_fields && p.missing_fields.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {p.missing_fields.slice(0, 3).map(f => (
                            <span key={f} className="rounded bg-amber-50 px-1.5 py-0.5 text-[10px] text-amber-600">{f}</span>
                          ))}
                          {p.missing_fields.length > 3 && (
                            <span className="text-[10px] text-amber-500">+{p.missing_fields.length - 3} more</span>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {catalogueStatus?.catalogue_ready && (
            <div className="p-4 border-t border-gray-100">
              <button onClick={() => router.push("/onboarding/match")}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-green-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-green-700">
                Next: Find SNP <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          )}
        </div>
      </div>

      <style jsx global>{`
        @keyframes fadeSlideUp {
          from { opacity: 0; transform: translateY(8px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}
