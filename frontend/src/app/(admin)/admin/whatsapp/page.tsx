"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import toast from "react-hot-toast";
import {
  Loader2, Plus, RefreshCw, Trash2, RotateCcw,
  CheckCircle, XCircle, Wifi, WifiOff, Smartphone,
} from "lucide-react";
import * as api from "@/lib/api";

interface Bot {
  id: string;
  label: string;
  phone_number: string | null;
  status: string;
  created_at: string;
}

interface BotStatus {
  connected: boolean;
  phone_number: string | null;
  status: string;
  qr_code: string | null;
}

export default function AdminWhatsAppPage() {
  const [bots, setBots] = useState<Bot[]>([]);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [activeBotId, setActiveBotId] = useState<string | null>(null);
  const [qrCode, setQrCode] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const loadBots = useCallback(async () => {
    try {
      const data = await api.adminListBots();
      setBots(data);
    } catch {
      toast.error("Failed to load bots");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadBots();
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [loadBots]);

  const startPolling = useCallback((botId: string) => {
    if (pollRef.current) clearInterval(pollRef.current);

    pollRef.current = setInterval(async () => {
      try {
        const status: BotStatus = await api.adminGetBotStatus(botId);

        if (status.qr_code) {
          setQrCode(status.qr_code);
        }

        if (status.connected) {
          if (pollRef.current) clearInterval(pollRef.current);
          pollRef.current = null;
          setActiveBotId(null);
          setQrCode(null);
          setConnecting(false);
          toast.success(`Connected! Phone: ${status.phone_number}`);
          loadBots();
        }
      } catch {
        /* polling error — ignore */
      }
    }, 3000);
  }, [loadBots]);

  const handleConnect = async () => {
    setConnecting(true);
    setQrCode(null);
    try {
      const result = await api.adminConnectBot("WhatsApp Bot");
      setActiveBotId(result.bot_id);

      if (result.connected) {
        toast.success("Already connected!");
        setConnecting(false);
        loadBots();
        return;
      }

      if (result.qr_code) {
        setQrCode(result.qr_code);
      }

      startPolling(result.bot_id);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Failed to connect bot";
      toast.error(msg);
      setConnecting(false);
    }
  };

  const handleDisconnect = async (botId: string) => {
    try {
      await api.adminDisconnectBot(botId);
      toast.success("Bot disconnected");
      loadBots();
    } catch {
      toast.error("Failed to disconnect");
    }
  };

  const handleReset = async (botId: string) => {
    try {
      const result = await api.adminResetBot(botId);
      setActiveBotId(botId);
      setConnecting(true);

      if (result.qr_code) {
        setQrCode(result.qr_code);
      }

      startPolling(botId);
      toast.success("Session reset — scan QR code");
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Failed to reset bot";
      toast.error(msg);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">WhatsApp Bots</h1>
          <p className="text-sm text-gray-500 mt-1">
            Manage WhatsApp bots for MSE catalogue follow-ups
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={loadBots}
            className="flex items-center gap-1.5 rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-600 hover:bg-gray-50"
          >
            <RefreshCw className="h-4 w-4" /> Refresh
          </button>
          <button
            onClick={handleConnect}
            disabled={connecting}
            className="flex items-center gap-1.5 rounded-lg bg-indigo-800 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-900 disabled:opacity-50"
          >
            {connecting ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Plus className="h-4 w-4" />
            )}
            Add Bot
          </button>
        </div>
      </div>

      {/* QR Code Modal */}
      {connecting && activeBotId && (
        <div className="mb-6 rounded-xl border-2 border-dashed border-indigo-200 bg-indigo-50 p-6">
          <div className="text-center">
            <Smartphone className="h-8 w-8 text-indigo-600 mx-auto mb-3" />
            <h3 className="text-lg font-semibold text-gray-900 mb-1">Scan QR Code</h3>
            <p className="text-sm text-gray-500 mb-4">
              Open WhatsApp on your phone → Settings → Linked Devices → Link a Device
            </p>
            {qrCode ? (
              <div className="inline-block bg-white rounded-xl p-4 shadow-sm">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={qrCode} alt="QR Code" className="w-64 h-64" />
              </div>
            ) : (
              <div className="flex items-center justify-center h-64">
                <div className="text-center">
                  <Loader2 className="h-8 w-8 animate-spin text-indigo-400 mx-auto mb-2" />
                  <p className="text-sm text-gray-400">Generating QR code...</p>
                </div>
              </div>
            )}
            <button
              onClick={() => {
                if (pollRef.current) clearInterval(pollRef.current);
                setConnecting(false);
                setActiveBotId(null);
                setQrCode(null);
              }}
              className="mt-4 text-sm text-gray-500 hover:text-gray-700 underline"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Bot List */}
      {bots.length === 0 && !connecting ? (
        <div className="text-center py-16 rounded-xl border border-gray-100 bg-gray-50">
          <WifiOff className="h-12 w-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500 font-medium">No WhatsApp bots connected</p>
          <p className="text-sm text-gray-400 mt-1">Click &quot;Add Bot&quot; to connect your WhatsApp</p>
        </div>
      ) : (
        <div className="space-y-3">
          {bots.map((bot) => (
            <div
              key={bot.id}
              className="flex items-center justify-between rounded-xl border border-gray-200 bg-white p-4 hover:shadow-sm transition-shadow"
            >
              <div className="flex items-center gap-4">
                <div
                  className={`flex h-10 w-10 items-center justify-center rounded-full ${
                    bot.status === "connected"
                      ? "bg-green-100 text-green-600"
                      : "bg-gray-100 text-gray-400"
                  }`}
                >
                  {bot.status === "connected" ? (
                    <Wifi className="h-5 w-5" />
                  ) : (
                    <WifiOff className="h-5 w-5" />
                  )}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-900">{bot.label}</span>
                    {bot.status === "connected" ? (
                      <span className="flex items-center gap-1 rounded-full bg-green-50 px-2 py-0.5 text-xs font-medium text-green-600">
                        <CheckCircle className="h-3 w-3" /> Connected
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-500">
                        <XCircle className="h-3 w-3" /> Disconnected
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-500 mt-0.5">
                    {bot.phone_number ? `+${bot.phone_number}` : "No phone linked"}
                    <span className="mx-2 text-gray-300">|</span>
                    <span className="text-xs text-gray-400">
                      Created {new Date(bot.created_at).toLocaleDateString()}
                    </span>
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleReset(bot.id)}
                  title="Reset (re-scan QR)"
                  className="flex h-8 w-8 items-center justify-center rounded-lg border border-gray-200 text-gray-400 hover:text-amber-600 hover:border-amber-200 hover:bg-amber-50 transition-colors"
                >
                  <RotateCcw className="h-4 w-4" />
                </button>
                <button
                  onClick={() => handleDisconnect(bot.id)}
                  title="Disconnect"
                  className="flex h-8 w-8 items-center justify-center rounded-lg border border-gray-200 text-gray-400 hover:text-red-600 hover:border-red-200 hover:bg-red-50 transition-colors"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
