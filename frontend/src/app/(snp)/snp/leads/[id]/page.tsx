"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";
import { Loader2, CheckCircle, XCircle, ArrowLeft } from "lucide-react";
import Link from "next/link";
import * as api from "@/lib/api";

export default function LeadDetailPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const [accepting, setAccepting] = useState(false);
  const [rejecting, setRejecting] = useState(false);
  const [done, setDone] = useState<"accepted" | "rejected" | null>(null);

  async function handleAccept() {
    setAccepting(true);
    try {
      await api.acceptLead(params.id);
      toast.success("Lead accepted! MSE will be notified.");
      setDone("accepted");
      setTimeout(() => router.push("/snp/leads"), 1500);
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setAccepting(false);
    }
  }

  async function handleReject() {
    setRejecting(true);
    try {
      await api.rejectLead(params.id);
      toast.success("Lead rejected.");
      setDone("rejected");
      setTimeout(() => router.push("/snp/leads"), 1500);
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setRejecting(false);
    }
  }

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <Link href="/snp/leads" className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 mb-6">
        <ArrowLeft className="h-4 w-4" /> Back to Leads
      </Link>

      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h1 className="text-xl font-bold text-gray-900 mb-1">MSE Lead Review</h1>
        <p className="text-sm text-gray-500 mb-6">MSE ID: {params.id}</p>

        {done ? (
          <div className={`text-center py-12 ${done === "accepted" ? "text-green-600" : "text-red-500"}`}>
            {done === "accepted"
              ? <><CheckCircle className="h-12 w-12 mx-auto mb-3" /><p className="font-medium">Lead Accepted!</p></>
              : <><XCircle className="h-12 w-12 mx-auto mb-3" /><p className="font-medium">Lead Rejected</p></>
            }
            <p className="text-sm text-gray-400 mt-1">Redirecting...</p>
          </div>
        ) : (
          <>
            <div className="rounded-lg bg-amber-50 border border-amber-200 p-4 mb-6">
              <p className="text-sm text-amber-700">
                <strong>Note:</strong> In the full demo, this page would show the MSE&apos;s complete profile,
                product catalogue with ONDC categories, compliance scores, and AI-generated readiness assessment.
              </p>
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleAccept}
                disabled={accepting || rejecting}
                className="flex items-center gap-2 rounded-lg bg-green-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-60"
              >
                {accepting ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle className="h-4 w-4" />}
                Accept MSE
              </button>
              <button
                onClick={handleReject}
                disabled={accepting || rejecting}
                className="flex items-center gap-2 rounded-lg border border-red-300 px-6 py-2.5 text-sm font-medium text-red-600 hover:bg-red-50 disabled:opacity-60"
              >
                {rejecting ? <Loader2 className="h-4 w-4 animate-spin" /> : <XCircle className="h-4 w-4" />}
                Reject
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
