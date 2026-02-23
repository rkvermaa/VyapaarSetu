"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import toast from "react-hot-toast";
import { Loader2, ChevronRight, Users } from "lucide-react";
import * as api from "@/lib/api";

export default function SNPLeadsPage() {
  const [leads, setLeads] = useState<unknown[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    api.getSNPLeads()
      .then(setLeads)
      .catch(() => toast.error("Failed to load leads"))
      .finally(() => setLoading(false));
  }, []);

  const filtered = leads.filter((l) => {
    const status = (l as Record<string, string>).status;
    if (filter === "all") return true;
    return status === filter;
  });

  if (loading) return (
    <div className="flex items-center justify-center h-full py-20">
      <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
    </div>
  );

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">MSE Leads</h1>
        <div className="flex gap-2">
          {["all", "suggested", "accepted", "rejected"].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`rounded-full px-4 py-1.5 text-sm font-medium capitalize transition-colors
                ${filter === f ? "bg-indigo-800 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"}`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center text-gray-400">
          <Users className="h-12 w-12 mx-auto mb-4 text-gray-200" />
          <p className="font-medium">No leads found</p>
          <p className="text-sm mt-1">Matched MSEs will appear here</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50">
                <th className="text-left text-xs font-semibold text-gray-500 uppercase tracking-wide px-4 py-3">Business</th>
                <th className="text-left text-xs font-semibold text-gray-500 uppercase tracking-wide px-4 py-3">State</th>
                <th className="text-left text-xs font-semibold text-gray-500 uppercase tracking-wide px-4 py-3">Category</th>
                <th className="text-left text-xs font-semibold text-gray-500 uppercase tracking-wide px-4 py-3">Match Score</th>
                <th className="text-left text-xs font-semibold text-gray-500 uppercase tracking-wide px-4 py-3">Status</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((lead, i) => {
                const l = lead as Record<string, unknown>;
                const mse = l.mse as Record<string, unknown> | undefined;
                return (
                  <tr key={i} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <p className="font-medium text-gray-800">{String(mse?.business_name || "—")}</p>
                      <p className="text-xs text-gray-400">{String(mse?.owner_name || "")}</p>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">{String(mse?.state || "—")}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{String(mse?.nic_code || "—")}</td>
                    <td className="px-4 py-3">
                      <span className="text-sm font-semibold text-indigo-700">
                        {typeof l.match_score === "number" ? `${l.match_score.toFixed(0)}%` : "—"}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`rounded-full px-3 py-1 text-xs font-medium capitalize
                        ${l.status === "accepted" ? "bg-green-100 text-green-700" :
                          l.status === "rejected" ? "bg-red-100 text-red-700" : "bg-amber-100 text-amber-700"}`}>
                        {String(l.status || "pending")}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <Link href={`/snp/leads/${String(mse?.id || i)}`}
                        className="flex items-center gap-1 text-sm text-indigo-600 hover:text-indigo-800">
                        Review <ChevronRight className="h-4 w-4" />
                      </Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
