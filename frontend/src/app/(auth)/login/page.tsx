"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import toast from "react-hot-toast";
import { Loader2 } from "lucide-react";
import * as api from "@/lib/api";
import { useAuthStore } from "@/store/auth";

export default function LoginPage() {
  const router = useRouter();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [mode, setMode] = useState<"login"|"register">("login");
  const [mobile, setMobile] = useState("");
  const [password, setPassword] = useState("");
  const [udyam, setUdyam] = useState("");
  const [loading, setLoading] = useState(false);
  const [udyamData, setUdyamData] = useState<Record<string,unknown>|null>(null);
  const [lookingUp, setLookingUp] = useState(false);

  const lookupUdyam = async () => {
    if (!udyam.trim()) return;
    setLookingUp(true);
    try {
      const res = await api.udyamLookup(udyam.trim());
      if (res.success && res.data) { setUdyamData(res.data); toast.success("Udyam details found!"); }
      else toast.error(res.error || "Udyam number not found");
    } catch { toast.error("Try: UDYAM-MH-01-0012345"); }
    finally { setLookingUp(false); }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const trimmedMobile = mobile.trim();
      if (mode === "register") {
        const res = await api.register(udyam, trimmedMobile, password.trim());
        setAuth(res.access_token, res.user_id, trimmedMobile, res.role);
        toast.success("Registered!"); router.push("/onboarding/profile");
      } else {
        const res = await api.login(trimmedMobile, password.trim());
        setAuth(res.access_token, res.user_id, trimmedMobile, res.role);
        toast.success("Welcome!");
        if (res.role === "snp") router.push("/snp/dashboard");
        else if (res.role === "admin") router.push("/admin/dashboard");
        else router.push("/dashboard");
      }
    } catch (err: unknown) { toast.error(err instanceof Error ? err.message : "Failed"); }
    finally { setLoading(false); }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-900 to-indigo-700 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-6">
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-xl bg-white/10 text-white font-bold text-xl mb-3">V</div>
          <h1 className="text-2xl font-bold text-white">VyapaarSetu</h1>
          <p className="text-indigo-200 text-sm">ONDC MSE Onboarding Platform</p>
        </div>
        <div className="bg-white rounded-2xl shadow-xl p-6">
          <div className="flex rounded-lg bg-gray-100 p-1 mb-6">
            {(["login","register"] as const).map((m) => (
              <button key={m} onClick={() => setMode(m)}
                className={`flex-1 rounded-md py-2 text-sm font-medium transition-colors ${mode===m?"bg-white shadow text-indigo-800":"text-gray-500"}`}>
                {m === "login" ? "Login" : "Register (MSE)"}
              </button>
            ))}
          </div>
          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === "register" && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Udyam Number</label>
                <div className="flex gap-2">
                  <input value={udyam} onChange={(e) => setUdyam(e.target.value.toUpperCase())}
                    placeholder="UDYAM-MH-01-0012345"
                    className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none" />
                  <button type="button" onClick={lookupUdyam} disabled={lookingUp}
                    className="rounded-lg bg-indigo-100 px-3 py-2 text-sm font-medium text-indigo-800 hover:bg-indigo-200 disabled:opacity-50">
                    {lookingUp ? <Loader2 className="h-4 w-4 animate-spin" /> : "Verify"}
                  </button>
                </div>
                {udyamData && (
                  <div className="mt-2 rounded-lg bg-green-50 border border-green-200 p-3 text-sm">
                    <div className="font-medium text-green-800">{String(udyamData.business_name)}</div>
                    <div className="text-green-600">{String(udyamData.owner_name)} - {String(udyamData.state)}</div>
                  </div>
                )}
              </div>
            )}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Mobile Number</label>
              <input value={mobile} onChange={(e) => setMobile(e.target.value)} placeholder="7409210692" required
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Enter password" required
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none" />
            </div>
            <button type="submit" disabled={loading}
              className="w-full rounded-lg bg-indigo-800 py-2.5 text-sm font-semibold text-white hover:bg-indigo-900 disabled:opacity-50 flex items-center justify-center gap-2">
              {loading && <Loader2 className="h-4 w-4 animate-spin" />}
              {mode === "register" ? "Create Account" : "Login"}
            </button>
          </form>
          <div className="mt-4 space-y-1 text-center text-xs text-gray-400">
            <div>MSE: <span className="font-mono">7409210692</span> / <span className="font-mono">demo1234</span></div>
            <div>SNP: <span className="font-mono">9000000001</span> / <span className="font-mono">snpdemo</span></div>
            <div>Admin: <span className="font-mono">9000000002</span> / <span className="font-mono">admindemo</span></div>
          </div>
        </div>
      </div>
    </div>
  );
}
