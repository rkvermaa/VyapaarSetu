"use client";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { Loader2, Users, Package, CheckCircle, TrendingUp } from "lucide-react";
import * as api from "@/lib/api";

function FunnelBar({ label, value, max, color }: { label: string; value: number; max: number; color: string }) {
  const pct = max > 0 ? (value / max) * 100 : 0;
  return (
    <div className="flex items-center gap-4">
      <div className="w-32 text-sm text-gray-600 text-right">{label}</div>
      <div className="flex-1 h-8 bg-gray-100 rounded-lg overflow-hidden">
        <div className={`h-full ${color} flex items-center px-3 text-white text-sm font-medium transition-all duration-500`}
          style={{ width: `${Math.max(pct, 4)}%` }}>
          {value}
        </div>
      </div>
      <div className="w-16 text-sm text-gray-400">{pct.toFixed(0)}%</div>
    </div>
  );
}

export default function AdminDashboardPage() {
  const [stats, setStats] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getAdminStats()
      .then(setStats)
      .catch(() => toast.error("Failed to load stats"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="flex items-center justify-center h-full py-20">
      <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
    </div>
  );

  const s = stats || {};
  const total = Number(s.total_mses || 0);
  const profileComplete = Number(s.profile_complete || 0);
  const catalogueReady = Number(s.catalogue_ready || 0);
  const matched = Number(s.matched || 0);
  const live = Number(s.live || 0);

  const cards = [
    { label: "Total Registered", value: total, icon: Users, color: "text-indigo-600 bg-indigo-50" },
    { label: "Catalogue Ready", value: catalogueReady, icon: Package, color: "text-amber-600 bg-amber-50" },
    { label: "SNP Matched", value: matched, icon: TrendingUp, color: "text-blue-600 bg-blue-50" },
    { label: "Live on ONDC", value: live, icon: CheckCircle, color: "text-green-600 bg-green-50" },
  ];

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">NSIC Admin Dashboard</h1>
        <p className="text-sm text-gray-500 mt-1">TEAM Initiative — MSE Onboarding Analytics</p>
      </div>

      <div className="grid grid-cols-4 gap-4 mb-8">
        {cards.map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="bg-white rounded-xl border border-gray-200 p-5">
            <div className={`inline-flex rounded-lg p-2 mb-3 ${color}`}>
              <Icon className="h-5 w-5" />
            </div>
            <div className="text-2xl font-bold text-gray-900">{value}</div>
            <div className="text-sm text-gray-500">{label}</div>
          </div>
        ))}
      </div>

      {/* Funnel */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
        <h2 className="font-semibold text-gray-800 mb-5">Onboarding Funnel</h2>
        <div className="space-y-3">
          <FunnelBar label="Registered" value={total} max={total} color="bg-indigo-600" />
          <FunnelBar label="Profile Done" value={profileComplete} max={total} color="bg-blue-500" />
          <FunnelBar label="Catalogue Ready" value={catalogueReady} max={total} color="bg-amber-500" />
          <FunnelBar label="SNP Matched" value={matched} max={total} color="bg-orange-500" />
          <FunnelBar label="Live on ONDC" value={live} max={total} color="bg-green-500" />
        </div>
      </div>

      {/* State breakdown if available */}
      {!!s.by_state && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="font-semibold text-gray-800 mb-4">Registrations by State</h2>
          <div className="grid grid-cols-3 gap-3">
            {Object.entries(s.by_state as Record<string, number>).map(([state, count]) => (
              <div key={state} className="flex justify-between items-center rounded-lg bg-gray-50 px-4 py-2">
                <span className="text-sm text-gray-700">{state}</span>
                <span className="font-semibold text-indigo-700">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
