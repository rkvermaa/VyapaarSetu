const API_BASE = "/api/v1";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = { ...(options.headers as Record<string, string>) };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (!(options.body instanceof FormData)) headers["Content-Type"] = "application/json";
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || body.error || `Request failed: ${res.status}`);
  }
  return res.json();
}

export interface AuthResponse { access_token: string; token_type: string; user_id: string; role: string; }
export function login(mobile: string, password: string) {
  return request<AuthResponse>("/auth/login", { method: "POST", body: JSON.stringify({ mobile, password }) });
}
export function register(udyam_number: string, mobile: string, password: string) {
  return request<AuthResponse>("/auth/register", { method: "POST", body: JSON.stringify({ udyam_number, mobile, password, role: "mse" }) });
}
export function udyamLookup(udyam_number: string) {
  return request<{ success: boolean; data?: Record<string, unknown>; error?: string }>("/auth/udyam-lookup", { method: "POST", body: JSON.stringify({ udyam_number }) });
}

export interface MSEProfile {
  id: string; udyam_number: string | null; business_name: string | null; owner_name: string | null;
  nic_code: string | null; major_activity: string | null; state: string | null; district: string | null;
  address: string | null; turnover: number | null; employee_count: number | null;
  transaction_type: string | null; target_states: string[] | null; whatsapp_number: string | null;
  onboarding_status: string; selected_snp_id: string | null;
}
export function getMSEProfile() { return request<MSEProfile>("/mse/profile"); }
export function updateMSEProfile(data: Partial<MSEProfile>) {
  return request<{ success: boolean; onboarding_status: string }>("/mse/profile", { method: "PUT", body: JSON.stringify(data) });
}
export function getMSEPassword() {
  return request<{ onboarding_status: string; steps: Array<{ step: string; label: string; completed: boolean }>; mse_id: string }>("/mse/status");
}
export function getMSEStatus() {
  return request<{ onboarding_status: string; steps: Array<{ step: string; label: string; completed: boolean }>; mse_id: string }>("/mse/status");
}
export function selectSNP(snp_id: string) {
  return request<{ success: boolean }>(`/mse/select-snp?snp_id=${snp_id}`, { method: "PUT" });
}

export interface Product {
  id: string; product_name: string | null; raw_description: string | null;
  ondc_category_code: string | null; subcategory: string | null;
  attributes: Record<string, unknown>; compliance_score: number | null;
  missing_fields: string[] | null; status: string; source: string; created_at: string;
}
export function listProducts() { return request<Product[]>("/products/"); }
export function addProduct(raw_description: string, source = "web") {
  return request<Product>("/products/", { method: "POST", body: JSON.stringify({ raw_description, source }) });
}
export function updateProduct(id: string, data: Partial<Product>) {
  return request<{ success: boolean; compliance_score: number }>(`/products/${id}`, { method: "PUT", body: JSON.stringify(data) });
}
export function deleteProduct(id: string) {
  return request<{ success: boolean }>(`/products/${id}`, { method: "DELETE" });
}
export function getCatalogueStatus() {
  return request<{ total_products: number; ready_products: number; draft_products: number; avg_compliance_score: number; catalogue_ready: boolean }>("/products/catalogue-status");
}

export interface CatalogueChatResponse { response: string; session_id: string; tool_calls_made: unknown[]; iterations: number; }
export function catalogueChat(message: string, channel = "web") {
  return request<CatalogueChatResponse>("/catalogue/chat", { method: "POST", body: JSON.stringify({ message, channel }) });
}

export interface SNPMatch {
  id: string; snp_id: string; match_score: number; match_reasons: string[];
  category_overlap_score: number; geography_score: number; status: string;
}
export function generateMatches() { return request<{ success: boolean; matches: unknown[]; matches_generated: number }>("/match/generate", { method: "POST" }); }
export function getRecommendations() { return request<SNPMatch[]>("/match/recommendations"); }

export function sendMessage(message: string, channel = "web") {
  return request<{ response: string; session_id: string }>("/chat/", { method: "POST", body: JSON.stringify({ message, channel }) });
}

export function getAdminStats() { return request<Record<string, unknown>>("/admin/stats"); }
export function getAdminQueue() { return request<unknown[]>("/admin/queue"); }
export function verifyMSE(mse_id: string, action: string) {
  return request<{ success: boolean }>(`/admin/verify/${mse_id}?action=${action}`, { method: "PUT" });
}

export function getSNPLeads() { return request<unknown[]>("/snp/leads"); }
export function acceptLead(mse_id: string) { return request<{ success: boolean }>(`/snp/leads/${mse_id}/accept`, { method: "PUT" }); }
export function rejectLead(mse_id: string) { return request<{ success: boolean }>(`/snp/leads/${mse_id}/reject`, { method: "PUT" }); }
