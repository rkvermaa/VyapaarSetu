"use client";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { Loader2, CheckCircle, XCircle, Users } from "lucide-react";
import * as api from "@/lib/api";

export default function AdminVerifyPage() {
  const [queue, setQueue] = useState<unknown[]>([]);
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState<string | null>(null);

  async function load() {
    try {
      const q = await api.getAdminQueue();
      setQueue(q);
    } catch {
      toast.error("Failed to load verification queue");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function handleVerify(mse_id: string, action: "approve" | "reject") {
    setVerifying(mse_id);
    try {
      await api.verifyMSE(mse_id, action);
      toast.success(action === "approve" ? "MSE approved!" : "MSE rejected");
      await load();
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setVerifying(null);
    }
  }

  if (loading) return (
    <div className="flex items-center justify-center h-full py-20">
      <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
    </div>
  );

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Verification Queue</h1>
          <p className="text-sm text-gray-500 mt-1">AI pre-screened MSE applications awaiting final approval</p>
        </div>
        <span className="rounded-full bg-amber-100 text-amber-700 px-4 py-1.5 text-sm font-medium">
          {queue.length} pending
        </span>
      </div>

      {queue.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center text-gray-400">
          <CheckCircle className="h-12 w-12 mx-auto mb-4 text-green-300" />
          <p className="font-medium text-gray-500">All clear!</p>
          <p className="text-sm mt-1">No applications pending verification</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50">
                <th className="text-left text-xs font-semibold text-gray-500 uppercase tracking-wide px-4 py-3">Business</th>
                <th className="text-left text-xs font-semibold text-gray-500 uppercase tracking-wide px-4 py-3">State</th>
                <th className="text-left text-xs font-semibold text-gray-500 uppercase tracking-wide px-4 py-3">AI Pre-Screen</th>
                <th className="text-left text-xs font-semibold text-gray-500 uppercase tracking-wide px-4 py-3">Submitted</th>
                <th className="px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {queue.map((item, i) => {
                const q = item as Record<string, unknown>;
                const mse = q.mse as Record<string, unknown> | undefined;
                const mse_id = String(mse?.id || i);
                return (
                  <tr key={i} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="px-4 py-4">
                      <p className="font-medium text-gray-800">{String(mse?.business_name || "—")}</p>
                      <p className="text-xs text-gray-400">{String(mse?.udyam_number || "")}</p>
                    </td>
                    <td className="px-4 py-4 text-sm text-gray-600">{String(mse?.state || "—")}</td>
                    <td className="px-4 py-4">
                      <div className="space-y-1">
                        <div className="flex items-center gap-1.5 text-xs text-green-600">
                          <CheckCircle className="h-3.5 w-3.5" /> Udyam verified
                        </div>
                        {!!q.catalogue_ready && (
                          <div className="flex items-center gap-1.5 text-xs text-green-600">
                            <CheckCircle className="h-3.5 w-3.5" /> Catalogue compliant
                          </div>
                        )}
                        {!!q.snp_matched && (
                          <div className="flex items-center gap-1.5 text-xs text-green-600">
                            <CheckCircle className="h-3.5 w-3.5" /> SNP matched
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-4 text-sm text-gray-500">
                      {q.submitted_at ? new Date(String(q.submitted_at)).toLocaleDateString("en-IN") : "—"}
                    </td>
                    <td className="px-4 py-4">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleVerify(mse_id, "approve")}
                          disabled={verifying === mse_id}
                          className="flex items-center gap-1 rounded-lg bg-green-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-green-700 disabled:opacity-60"
                        >
                          {verifying === mse_id ? <Loader2 className="h-3 w-3 animate-spin" /> : <CheckCircle className="h-3 w-3" />}
                          Approve
                        </button>
                        <button
                          onClick={() => handleVerify(mse_id, "reject")}
                          disabled={verifying === mse_id}
                          className="flex items-center gap-1 rounded-lg border border-red-300 px-3 py-1.5 text-xs font-medium text-red-600 hover:bg-red-50 disabled:opacity-60"
                        >
                          <XCircle className="h-3 w-3" />
                          Reject
                        </button>
                      </div>
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
