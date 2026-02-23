"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { CheckCircle, Circle, ArrowRight, Package, Building2 } from "lucide-react";
import * as api from "@/lib/api";

const STATUS_LABELS: Record<string, string> = {
  registered: "Registered", profile_complete: "Profile Complete",
  catalogue_ready: "Catalogue Ready", snp_selected: "SNP Selected",
  submitted: "Submitted", under_review: "Under Review", live: "Live on ONDC",
};

export default function DashboardPage() {
  const [status, setStatus] = useState<{ onboarding_status: string; steps: { step: string; label: string; completed: boolean }[] } | null>(null);
  const [catalogue, setCatalogue] = useState<{ total_products: number; ready_products: number; avg_compliance_score: number } | null>(null);

  useEffect(() => {
    api.getMSEStatus().then(setStatus).catch(() => {});
    api.getCatalogueStatus().then(setCatalogue).catch(() => {});
  }, []);

  const currentStatus = status?.onboarding_status || "registered";

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">My Onboarding Dashboard</h1>
        <p className="text-gray-500 text-sm mt-1">Track your ONDC onboarding journey</p>
      </div>

      <div className="mb-6 inline-flex items-center gap-2 rounded-full bg-indigo-100 px-4 py-2 text-sm font-medium text-indigo-800">
        <div className="h-2 w-2 rounded-full bg-indigo-600 animate-pulse" />
        Status: {STATUS_LABELS[currentStatus] || currentStatus}
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
        <h2 className="font-semibold text-gray-900 mb-4">Onboarding Progress</h2>
        <div className="space-y-3">
          {(status?.steps || []).map((step) => (
            <div key={step.step} className="flex items-center gap-3">
              {step.completed
                ? <CheckCircle className="h-5 w-5 text-green-500 shrink-0" />
                : <Circle className="h-5 w-5 text-gray-300 shrink-0" />}
              <span className={`text-sm ${step.completed ? "text-gray-900 font-medium" : "text-gray-400"}`}>
                {step.label}
              </span>
              {step.step === currentStatus && (
                <span className="ml-auto text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full">Current</span>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="grid sm:grid-cols-2 gap-4">
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="flex items-center gap-2 mb-3">
            <Package className="h-5 w-5 text-indigo-800" />
            <h3 className="font-semibold text-gray-900">My Catalogue</h3>
          </div>
          <div className="text-3xl font-bold text-indigo-800 mb-1">{catalogue?.total_products || 0}</div>
          <div className="text-sm text-gray-500 mb-1">{catalogue?.ready_products || 0} ready - avg {catalogue?.avg_compliance_score?.toFixed(0) || 0}% compliant</div>
          <Link href="/onboarding/catalogue" className="mt-3 flex items-center gap-1 text-sm text-indigo-600 hover:text-indigo-800">
            Add products <ArrowRight className="h-3 w-3" />
          </Link>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="flex items-center gap-2 mb-3">
            <Building2 className="h-5 w-5 text-indigo-800" />
            <h3 className="font-semibold text-gray-900">SNP Matching</h3>
          </div>
          <p className="text-sm text-gray-500 mb-3">Find the best SNP platform for your business</p>
          <Link href="/onboarding/match" className="flex items-center gap-1 text-sm text-indigo-600 hover:text-indigo-800">
            View recommendations <ArrowRight className="h-3 w-3" />
          </Link>
        </div>
      </div>

      {currentStatus === "profile_complete" && (
        <div className="mt-4 rounded-xl bg-yellow-50 border border-yellow-200 p-4 flex items-center justify-between">
          <div>
            <div className="font-medium text-yellow-900">Next: Add your products</div>
            <div className="text-sm text-yellow-700">Build your ONDC catalogue to continue</div>
          </div>
          <Link href="/onboarding/catalogue" className="rounded-lg bg-yellow-500 px-4 py-2 text-sm font-medium text-white hover:bg-yellow-400">
            Add Products
          </Link>
        </div>
      )}
      {currentStatus === "catalogue_ready" && (
        <div className="mt-4 rounded-xl bg-green-50 border border-green-200 p-4 flex items-center justify-between">
          <div>
            <div className="font-medium text-green-900">Next: Select your SNP</div>
            <div className="text-sm text-green-700">Get AI recommendations for the best platform</div>
          </div>
          <Link href="/onboarding/match" className="rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700">
            Get Matched
          </Link>
        </div>
      )}
    </div>
  );
}
