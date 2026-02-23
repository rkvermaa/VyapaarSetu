"use client";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { Loader2, Users, CheckCircle, Clock, TrendingUp } from "lucide-react";
import * as api from "@/lib/api";

export default function SNPDashboardPage() {
  const [leads, setLeads] = useState<unknown[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getSNPLeads()
      .then(setLeads)
      .catch(() => toast.error("Failed to load leads"))
      .finally(() => setLoading(false));
  }, []);

  const accepted = leads.filter((l) => (l as Record<string,string>).status === "accepted").length;
  const pending = leads.filter((l) => (l as Record<string,string>).status === "suggested").length;
  const rejected = leads.filter((l) => (l as Record<string,string>).status === "rejected").length;

  if (loading) return (
    <div className="flex items-center justify-center h-full py-20">
      <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
    </div>
  );

  const stats = [
    { label: "Total Leads", value: leads.length, icon: Users, color: "bg-indigo-50 text-indigo-700" },
    { label: "Pending Review", value: pending, icon: Clock, color: "bg-amber-50 text-amber-700" },
    { label: "Accepted", value: accepted, icon: CheckCircle, color: "bg-green-50 text-green-700" },
    { label: "Rejected", value: rejected, icon: TrendingUp, color: "bg-red-50 text-red-700" },
  ];

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">SNP Dashboard</h1>

      <div className="grid grid-cols-4 gap-4 mb-8">
        {stats.map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="bg-white rounded-xl border border-gray-200 p-5">
            <div className={`inline-flex rounded-lg p-2 mb-3 ${color}`}>
              <Icon className="h-5 w-5" />
            </div>
            <div className="text-2xl font-bold text-gray-900">{value}</div>
            <div className="text-sm text-gray-500">{label}</div>
          </div>
        ))}
      </div>

      {/* Recent Leads */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <h2 className="font-semibold text-gray-800 mb-4">Recent Matched Leads</h2>
        {leads.length === 0 ? (
          <div className="text-center py-8 text-gray-400">
            <Users className="h-10 w-10 mx-auto mb-3 text-gray-200" />
            <p>No leads yet. MSEs will appear here when matched to your SNP.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {leads.slice(0, 5).map((lead, i) => {
              const l = lead as Record<string, unknown>;
              const mse = l.mse as Record<string, unknown> | undefined;
              return (
                <div key={i} className="flex items-center justify-between rounded-lg border border-gray-100 p-4 hover:bg-gray-50">
                  <div>
                    <p className="font-medium text-gray-800">{String(mse?.business_name || "Unknown MSE")}</p>
                    <p className="text-sm text-gray-500">{String(mse?.state || "")} • {String(mse?.major_activity || "")}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-semibold text-indigo-700">
                      {typeof l.match_score === "number" ? `${l.match_score.toFixed(0)}% match` : ""}
                    </span>
                    <span className={`rounded-full px-3 py-1 text-xs font-medium
                      ${l.status === "accepted" ? "bg-green-100 text-green-700" :
                        l.status === "rejected" ? "bg-red-100 text-red-700" : "bg-amber-100 text-amber-700"}`}>
                      {String(l.status || "pending")}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
