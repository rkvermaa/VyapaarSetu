"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";
import { Loader2, Star, MapPin, Clock, CheckCircle, RefreshCw } from "lucide-react";
import * as api from "@/lib/api";

const SNP_COLORS: Record<string, string> = {
  "GlobalLinker": "bg-blue-100 text-blue-800",
  "Plotch": "bg-purple-100 text-purple-800",
  "SellerApp": "bg-green-100 text-green-800",
  "eSamudaay": "bg-orange-100 text-orange-800",
  "DotPe": "bg-red-100 text-red-800",
  "MyStore": "bg-teal-100 text-teal-800",
};

function ScoreCircle({ score }: { score: number }) {
  const r = 32;
  const circ = 2 * Math.PI * r;
  const dash = (score / 100) * circ;
  const color = score >= 80 ? "#16a34a" : score >= 60 ? "#d97706" : "#dc2626";
  return (
    <div className="relative flex h-20 w-20 items-center justify-center">
      <svg className="absolute inset-0 -rotate-90" width="80" height="80">
        <circle cx="40" cy="40" r={r} fill="none" stroke="#e5e7eb" strokeWidth="6" />
        <circle cx="40" cy="40" r={r} fill="none" stroke={color} strokeWidth="6"
          strokeDasharray={`${dash} ${circ}`} strokeLinecap="round" />
      </svg>
      <div className="text-center">
        <div className="text-lg font-bold text-gray-800">{score.toFixed(0)}</div>
        <div className="text-xs text-gray-400">/ 100</div>
      </div>
    </div>
  );
}

export default function MatchPage() {
  const router = useRouter();
  const [matches, setMatches] = useState<api.SNPMatch[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [selecting, setSelecting] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);

  async function loadMatches() {
    try {
      const recs = await api.getRecommendations();
      setMatches(recs);
    } catch {
      // No matches yet
    } finally {
      setLoading(false);
    }
  }

  async function generate() {
    setGenerating(true);
    try {
      await api.generateMatches();
      toast.success("SNP recommendations generated!");
      await loadMatches();
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setGenerating(false);
    }
  }

  useEffect(() => { loadMatches(); }, []);

  async function handleSelect(snp_id: string) {
    if (!confirm("Select this SNP? Your profile and catalogue will be shared with them.")) return;
    setSelecting(snp_id);
    try {
      await api.selectSNP(snp_id);
      setSelected(snp_id);
      toast.success("SNP selected! Onboarding initiated.");
      setTimeout(() => router.push("/dashboard"), 1500);
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setSelecting(null);
    }
  }

  if (loading) return (
    <div className="flex items-center justify-center h-full py-20">
      <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
    </div>
  );

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Progress */}
      <div className="mb-6">
        <div className="flex items-center gap-2">
          {["Profile", "Catalogue", "SNP Match"].map((step, i) => (
            <div key={step} className="flex items-center gap-2">
              <div className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold
                ${i === 2 ? "bg-indigo-800 text-white" : "bg-green-500 text-white"}`}>
                {i < 2 ? "✓" : "3"}
              </div>
              <span className={`text-sm ${i === 2 ? "text-indigo-800 font-medium" : "text-gray-400"}`}>{step}</span>
              {i < 2 && <div className="w-8 h-0.5 bg-gray-200" />}
            </div>
          ))}
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h1 className="text-xl font-bold text-gray-900">Find Your Best SNP</h1>
            <p className="text-sm text-gray-500 mt-1">
              AI analyses your profile and catalogue to recommend the best Seller Network Participants.
            </p>
          </div>
          <button
            onClick={generate}
            disabled={generating}
            className="flex items-center gap-2 rounded-lg border border-indigo-300 px-4 py-2 text-sm font-medium text-indigo-700 hover:bg-indigo-50 disabled:opacity-60"
          >
            {generating ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
            {matches.length === 0 ? "Generate Recommendations" : "Refresh"}
          </button>
        </div>

        {matches.length === 0 ? (
          <div className="text-center py-16 text-gray-400">
            <Star className="h-12 w-12 mx-auto mb-4 text-gray-200" />
            <p className="font-medium text-gray-500">No recommendations yet</p>
            <p className="text-sm mt-1">Complete your catalogue first, then generate SNP recommendations</p>
          </div>
        ) : (
          <div className="space-y-4">
            {matches.map((match, idx) => {
              const snpName = (match as unknown as Record<string, string>).snp_name || `SNP ${idx + 1}`;
              const colorClass = SNP_COLORS[snpName] || "bg-gray-100 text-gray-800";
              const isSelected = selected === match.snp_id;
              return (
                <div
                  key={match.id}
                  className={`rounded-xl border-2 p-5 transition-colors
                    ${isSelected ? "border-green-400 bg-green-50" : idx === 0 ? "border-indigo-300 bg-indigo-50/30" : "border-gray-200"}`}
                >
                  {idx === 0 && !isSelected && (
                    <div className="mb-3 inline-flex items-center gap-1 rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-700">
                      <Star className="h-3 w-3" /> Best Match
                    </div>
                  )}
                  {isSelected && (
                    <div className="mb-3 inline-flex items-center gap-1 rounded-full bg-green-100 px-3 py-1 text-xs font-medium text-green-700">
                      <CheckCircle className="h-3 w-3" /> Selected
                    </div>
                  )}

                  <div className="flex items-start gap-5">
                    <ScoreCircle score={match.match_score} />

                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className={`rounded-full px-3 py-1 text-sm font-bold ${colorClass}`}>{snpName}</span>
                        <span className="text-xs text-gray-400">
                          {(match as unknown as Record<string, string>).avg_onboarding_days
                            ? `~${(match as unknown as Record<string, string>).avg_onboarding_days} days onboarding`
                            : ""}
                        </span>
                      </div>

                      <div className="grid grid-cols-3 gap-3 mb-3">
                        <div className="text-center rounded-lg bg-white border border-gray-100 py-2">
                          <div className="text-sm font-semibold text-indigo-700">{match.category_overlap_score?.toFixed(0) ?? "-"}%</div>
                          <div className="text-xs text-gray-400">Category Match</div>
                        </div>
                        <div className="text-center rounded-lg bg-white border border-gray-100 py-2">
                          <div className="text-sm font-semibold text-indigo-700">{match.geography_score?.toFixed(0) ?? "-"}%</div>
                          <div className="text-xs text-gray-400">Geography</div>
                        </div>
                        <div className="text-center rounded-lg bg-white border border-gray-100 py-2">
                          <div className="text-sm font-semibold text-indigo-700">{match.match_score.toFixed(0)}%</div>
                          <div className="text-xs text-gray-400">Overall Score</div>
                        </div>
                      </div>

                      {match.match_reasons && match.match_reasons.length > 0 && (
                        <ul className="space-y-1">
                          {match.match_reasons.slice(0, 4).map((reason, r) => (
                            <li key={r} className="flex items-start gap-2 text-sm text-gray-600">
                              <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                              {reason}
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>

                    <div className="flex-shrink-0">
                      {isSelected ? (
                        <div className="flex items-center gap-1 text-green-600 text-sm font-medium">
                          <CheckCircle className="h-5 w-5" /> Selected
                        </div>
                      ) : (
                        <button
                          onClick={() => handleSelect(match.snp_id)}
                          disabled={selecting === match.snp_id || !!selected}
                          className="rounded-lg bg-indigo-800 px-5 py-2.5 text-sm font-medium text-white hover:bg-indigo-900 disabled:opacity-50"
                        >
                          {selecting === match.snp_id ? <Loader2 className="h-4 w-4 animate-spin" /> : "Select"}
                        </button>
                      )}
                    </div>
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
