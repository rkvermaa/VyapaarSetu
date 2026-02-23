"use client";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";
import { Loader2, Plus, Trash2, ChevronRight, CheckCircle, AlertCircle, Clock } from "lucide-react";
import * as api from "@/lib/api";
import ChatPanel from "@/components/chat/ChatPanel";

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

export default function CataloguePage() {
  const router = useRouter();
  const [products, setProducts] = useState<api.Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const [selected, setSelected] = useState<api.Product | null>(null);
  const [catalogueStatus, setCatalogueStatus] = useState<{ total_products: number; ready_products: number; avg_compliance_score: number; catalogue_ready: boolean } | null>(null);
  const descRef = useRef<HTMLInputElement>(null);

  async function load() {
    try {
      const [prods, status] = await Promise.all([api.listProducts(), api.getCatalogueStatus()]);
      setProducts(prods);
      setCatalogueStatus(status);
      if (prods.length > 0 && !selected) setSelected(prods[0]);
    } catch {
      toast.error("Failed to load products");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  async function handleAddProduct() {
    const desc = descRef.current?.value?.trim();
    if (!desc) { toast.error("Please describe your product first"); return; }
    setAdding(true);
    try {
      const prod = await api.addProduct(desc);
      toast.success("Product added and AI-classified!");
      descRef.current!.value = "";
      await load();
      setSelected(prod);
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setAdding(false);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("Remove this product?")) return;
    try {
      await api.deleteProduct(id);
      toast.success("Product removed");
      setSelected(null);
      load();
    } catch {
      toast.error("Failed to delete");
    }
  }

  function handleChatSuccess() {
    load();
  }

  if (loading) return (
    <div className="flex items-center justify-center h-full py-20">
      <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
    </div>
  );

  return (
    <div className="flex h-screen flex-col">
      {/* Progress */}
      <div className="px-6 pt-6 pb-2 border-b border-gray-200 bg-white">
        <div className="flex items-center gap-2 mb-3">
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
              <span className="flex items-center gap-1 text-green-600 font-medium">
                <CheckCircle className="h-4 w-4" /> Catalogue ready!
              </span>
            )}
          </div>
        )}
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Left: Product list */}
        <div className="w-72 border-r border-gray-200 bg-white flex flex-col">
          <div className="p-4 border-b border-gray-100">
            <h2 className="font-semibold text-gray-800 mb-3">Products</h2>
            {/* Quick add */}
            <div className="flex gap-2">
              <input
                ref={descRef}
                placeholder="Describe product..."
                className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500"
                onKeyDown={(e) => e.key === "Enter" && handleAddProduct()}
              />
              <button
                onClick={handleAddProduct}
                disabled={adding}
                className="rounded-lg bg-indigo-800 px-3 py-2 text-white hover:bg-indigo-900 disabled:opacity-60"
              >
                {adding ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
              </button>
            </div>
            <p className="text-xs text-gray-400 mt-1">Or use the AI chat to add products</p>
          </div>

          <div className="flex-1 overflow-y-auto p-3 space-y-2">
            {products.length === 0 ? (
              <div className="text-center py-8 text-gray-400">
                <p className="text-sm">No products yet</p>
                <p className="text-xs mt-1">Add your first product above or via chat</p>
              </div>
            ) : (
              products.map((p) => (
                <button
                  key={p.id}
                  onClick={() => setSelected(p)}
                  className={`w-full text-left rounded-lg p-3 border transition-colors
                    ${selected?.id === p.id ? "border-indigo-300 bg-indigo-50" : "border-gray-100 hover:bg-gray-50"}`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-800 truncate">
                        {p.product_name || "Unnamed product"}
                      </p>
                      <p className="text-xs text-gray-400 mt-0.5 truncate">{p.ondc_category_code || "Classifying..."}</p>
                    </div>
                    <div className="flex items-center gap-1 flex-shrink-0">
                      <StatusIcon status={p.status} />
                      <ComplianceBadge score={p.compliance_score} />
                    </div>
                  </div>
                </button>
              ))
            )}
          </div>

          {catalogueStatus?.catalogue_ready && (
            <div className="p-4 border-t border-gray-100">
              <button
                onClick={() => router.push("/onboarding/match")}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-green-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-green-700"
              >
                Next: Find SNP <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          )}
        </div>

        {/* Right: Product detail + AI chat */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {selected ? (
            <div className="flex-1 overflow-y-auto p-6">
              <div className="bg-white rounded-xl border border-gray-200 p-5 mb-4">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-semibold text-gray-900 text-lg">{selected.product_name || "Product"}</h3>
                    <p className="text-sm text-gray-500 mt-0.5">{selected.raw_description}</p>
                  </div>
                  <button onClick={() => handleDelete(selected.id)} className="text-red-400 hover:text-red-600 p-1">
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>

                <div className="mt-4 grid grid-cols-2 gap-3">
                  {selected.ondc_category_code && (
                    <div className="rounded-lg bg-indigo-50 p-3">
                      <p className="text-xs text-indigo-500 font-medium">ONDC Category</p>
                      <p className="text-sm font-semibold text-indigo-800 mt-0.5">{selected.ondc_category_code}</p>
                      {selected.subcategory && <p className="text-xs text-indigo-600">{selected.subcategory}</p>}
                    </div>
                  )}
                  <div className="rounded-lg bg-gray-50 p-3">
                    <p className="text-xs text-gray-500 font-medium">Compliance Score</p>
                    <div className="flex items-center gap-2 mt-1">
                      <div className="flex-1 h-2 rounded-full bg-gray-200">
                        <div
                          className={`h-2 rounded-full ${(selected.compliance_score || 0) >= 80 ? "bg-green-500" : (selected.compliance_score || 0) >= 50 ? "bg-amber-500" : "bg-red-500"}`}
                          style={{ width: `${selected.compliance_score || 0}%` }}
                        />
                      </div>
                      <span className="text-sm font-semibold">{(selected.compliance_score || 0).toFixed(0)}%</span>
                    </div>
                  </div>
                </div>

                {selected.missing_fields && selected.missing_fields.length > 0 && (
                  <div className="mt-4 rounded-lg bg-amber-50 border border-amber-200 p-3">
                    <p className="text-sm font-medium text-amber-800 mb-2">
                      <AlertCircle className="h-4 w-4 inline mr-1" />
                      Missing Fields ({selected.missing_fields.length})
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {selected.missing_fields.map((f) => (
                        <span key={f} className="rounded-full bg-amber-100 px-3 py-1 text-xs text-amber-700 font-medium">{f}</span>
                      ))}
                    </div>
                  </div>
                )}

                {selected.attributes && Object.keys(selected.attributes).length > 0 && (
                  <div className="mt-4">
                    <p className="text-sm font-medium text-gray-700 mb-2">Extracted Attributes</p>
                    <div className="grid grid-cols-2 gap-2">
                      {Object.entries(selected.attributes).map(([k, v]) => (
                        <div key={k} className="flex justify-between text-sm bg-gray-50 rounded-lg px-3 py-1.5">
                          <span className="text-gray-500 capitalize">{k.replace(/_/g, " ")}</span>
                          <span className="font-medium text-gray-800">{String(v)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="flex-1 flex items-center justify-center text-gray-400">
              <div className="text-center">
                <Package className="h-12 w-12 mx-auto mb-3 text-gray-200" />
                <p>Select a product to view details</p>
              </div>
            </div>
          )}

          {/* AI Chat */}
          <div className="h-72 border-t border-gray-200">
            <ChatPanel
              placeholder="Describe your product in Hindi or English... e.g. 'Peetal ke diye banata hoon, Rs 150'"
              initialMessage="Namaste! Apne product describe karein — main ONDC category, attributes aur compliance check kar doonga."
              onSendMessage={async (msg) => {
                const res = await api.catalogueChat(msg);
                handleChatSuccess();
                return res.response;
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

// Needed for the empty state icon
function Package({ className }: { className?: string }) {
  return <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 10V11" /></svg>;
}
