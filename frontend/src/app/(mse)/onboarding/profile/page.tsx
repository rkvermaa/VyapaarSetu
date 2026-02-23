"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";
import { Loader2, Save, Mic } from "lucide-react";
import * as api from "@/lib/api";
import VoiceInput from "@/components/voice/VoiceInput";

const STATES = [
  "Andhra Pradesh","Arunachal Pradesh","Assam","Bihar","Chhattisgarh","Goa","Gujarat",
  "Haryana","Himachal Pradesh","Jharkhand","Karnataka","Kerala","Madhya Pradesh",
  "Maharashtra","Manipur","Meghalaya","Mizoram","Nagaland","Odisha","Punjab",
  "Rajasthan","Sikkim","Tamil Nadu","Telangana","Tripura","Uttar Pradesh",
  "Uttarakhand","West Bengal","Delhi","J&K","Ladakh",
];

export default function ProfilePage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showVoice, setShowVoice] = useState<string | null>(null);
  const [form, setForm] = useState({
    business_name: "", owner_name: "", nic_code: "", major_activity: "manufacturing",
    state: "", district: "", address: "", turnover: "", employee_count: "",
    transaction_type: "b2c", target_states: [] as string[], whatsapp_number: "",
  });

  useEffect(() => {
    api.getMSEProfile()
      .then((p) => {
        setForm({
          business_name: p.business_name || "",
          owner_name: p.owner_name || "",
          nic_code: p.nic_code || "",
          major_activity: p.major_activity || "manufacturing",
          state: p.state || "",
          district: p.district || "",
          address: p.address || "",
          turnover: p.turnover ? String(p.turnover) : "",
          employee_count: p.employee_count ? String(p.employee_count) : "",
          transaction_type: p.transaction_type || "b2c",
          target_states: p.target_states || [],
          whatsapp_number: p.whatsapp_number || "",
        });
      })
      .catch(() => toast.error("Failed to load profile"))
      .finally(() => setLoading(false));
  }, []);

  function set(field: string, value: unknown) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  function toggleTargetState(s: string) {
    setForm((f) => ({
      ...f,
      target_states: f.target_states.includes(s)
        ? f.target_states.filter((x) => x !== s)
        : [...f.target_states, s],
    }));
  }

  async function handleSave() {
    if (!form.business_name || !form.state) {
      toast.error("Business name and state are required");
      return;
    }
    setSaving(true);
    try {
      await api.updateMSEProfile({
        ...form,
        turnover: form.turnover ? Number(form.turnover) : undefined,
        employee_count: form.employee_count ? Number(form.employee_count) : undefined,
      } as Partial<api.MSEProfile>);
      toast.success("Profile saved!");
      router.push("/onboarding/catalogue");
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setSaving(false);
    }
  }

  if (loading) return (
    <div className="flex items-center justify-center h-full py-20">
      <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
    </div>
  );

  return (
    <div className="max-w-3xl mx-auto p-6">
      {/* Progress */}
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-2">
          {["Profile", "Catalogue", "SNP Match"].map((step, i) => (
            <div key={step} className="flex items-center gap-2">
              <div className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold
                ${i === 0 ? "bg-indigo-800 text-white" : "bg-gray-200 text-gray-500"}`}>
                {i + 1}
              </div>
              <span className={`text-sm ${i === 0 ? "text-indigo-800 font-medium" : "text-gray-400"}`}>{step}</span>
              {i < 2 && <div className="w-8 h-0.5 bg-gray-200" />}
            </div>
          ))}
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h1 className="text-xl font-bold text-gray-900 mb-1">Business Profile</h1>
        <p className="text-sm text-gray-500 mb-6">
          Your Udyam details are pre-filled. Review and complete the remaining fields.
        </p>

        <div className="grid grid-cols-2 gap-4">
          {/* Business Name */}
          <div className="col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Business Name <span className="text-red-500">*</span>
            </label>
            <div className="flex gap-2">
              <input
                value={form.business_name}
                onChange={(e) => set("business_name", e.target.value)}
                className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="Your registered business name"
              />
              <button onClick={() => setShowVoice("business_name")}
                className="rounded-lg border border-gray-300 px-3 py-2 hover:bg-gray-50">
                <Mic className="h-4 w-4 text-gray-500" />
              </button>
            </div>
            {showVoice === "business_name" && (
              <VoiceInput onTranscript={(t) => { set("business_name", t); setShowVoice(null); }} />
            )}
          </div>

          {/* Owner Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Owner / Proprietor Name</label>
            <input
              value={form.owner_name}
              onChange={(e) => set("owner_name", e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="Proprietor/Director name"
            />
          </div>

          {/* NIC Code */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">NIC Code</label>
            <input
              value={form.nic_code}
              onChange={(e) => set("nic_code", e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="e.g. 25910"
            />
          </div>

          {/* Major Activity */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Major Activity</label>
            <select
              value={form.major_activity}
              onChange={(e) => set("major_activity", e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="manufacturing">Manufacturing</option>
              <option value="services">Services</option>
            </select>
          </div>

          {/* Transaction Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Transaction Type</label>
            <select
              value={form.transaction_type}
              onChange={(e) => set("transaction_type", e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="b2c">B2C (Consumer)</option>
              <option value="b2b">B2B (Business)</option>
              <option value="both">Both B2B + B2C</option>
            </select>
          </div>

          {/* State */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              State <span className="text-red-500">*</span>
            </label>
            <select
              value={form.state}
              onChange={(e) => set("state", e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">Select state</option>
              {STATES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>

          {/* District */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">District</label>
            <input
              value={form.district}
              onChange={(e) => set("district", e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="e.g. Pune"
            />
          </div>

          {/* Address */}
          <div className="col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">Address</label>
            <input
              value={form.address}
              onChange={(e) => set("address", e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="Factory/Office address"
            />
          </div>

          {/* Turnover */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Annual Turnover (₹)</label>
            <input
              type="number"
              value={form.turnover}
              onChange={(e) => set("turnover", e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="e.g. 5000000"
            />
          </div>

          {/* Employee Count */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Employee Count</label>
            <input
              type="number"
              value={form.employee_count}
              onChange={(e) => set("employee_count", e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="e.g. 12"
            />
          </div>

          {/* WhatsApp */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">WhatsApp Number</label>
            <input
              value={form.whatsapp_number}
              onChange={(e) => set("whatsapp_number", e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="+91 98765 43210"
            />
          </div>
        </div>

        {/* Target States */}
        <div className="mt-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Target States (where you want to sell)
          </label>
          <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto rounded-lg border border-gray-200 p-3">
            {STATES.map((s) => (
              <button
                key={s}
                onClick={() => toggleTargetState(s)}
                className={`rounded-full px-3 py-1 text-xs font-medium transition-colors
                  ${form.target_states.includes(s)
                    ? "bg-indigo-800 text-white"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"}`}
              >
                {s}
              </button>
            ))}
          </div>
          {form.target_states.length > 0 && (
            <p className="text-xs text-indigo-600 mt-1">{form.target_states.length} states selected</p>
          )}
        </div>

        <div className="mt-6 flex justify-end">
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-2 rounded-lg bg-indigo-800 px-6 py-2.5 text-sm font-medium text-white hover:bg-indigo-900 disabled:opacity-60"
          >
            {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
            Save & Continue
          </button>
        </div>
      </div>
    </div>
  );
}
