"use client";
import Link from "next/link";
import { ArrowRight, Mic, Tag, Users, CheckCircle, Building2 } from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      <nav className="border-b border-gray-200 bg-white px-6 py-4">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-800 text-white font-bold text-sm">V</div>
            <span className="font-bold text-xl text-indigo-800">VyapaarSetu</span>
            <span className="text-xs text-gray-400 ml-1">&#x0935;&#x094D;&#x092F;&#x093E;&#x092A;&#x093E;&#x0930; &#x0938;&#x0947;&#x0924;&#x0941;</span>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/login" className="text-sm text-gray-600 hover:text-indigo-800">Login</Link>
            <Link href="/login" className="rounded-lg bg-indigo-800 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-900">
              Register Free
            </Link>
          </div>
        </div>
      </nav>

      <section className="bg-gradient-to-br from-indigo-900 to-indigo-700 px-6 py-20 text-white">
        <div className="mx-auto max-w-4xl text-center">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-yellow-400/20 px-4 py-1.5 text-yellow-300 text-sm">
            <CheckCircle className="h-4 w-4" /> TEAM Initiative — Government of India
          </div>
          <h1 className="mb-4 text-4xl font-bold leading-tight md:text-5xl">&#x0905;&#x092A;&#x0928;&#x093E; &#x0935;&#x094D;&#x092F;&#x093E;&#x092A;&#x093E;&#x0930; ONDC &#x092A;&#x0930; &#x0932;&#x093E;&#x090F;&#x0902;</h1>
          <p className="mb-3 text-xl text-indigo-200">Bring Your Business to ONDC</p>
          <p className="mb-8 text-indigo-200 max-w-2xl mx-auto">
            AI-powered onboarding for Micro &amp; Small Enterprises. Voice-enabled registration,
            intelligent product cataloguing, and smart SNP matching — all free under TEAM scheme.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link href="/login" className="flex items-center gap-2 rounded-xl bg-yellow-500 px-8 py-3 font-semibold text-white hover:bg-yellow-400 transition-colors">
              Start Free Registration <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
          <p className="mt-4 text-sm text-indigo-300">Free for MSEs &nbsp;· Udyam registration required &nbsp;· Government scheme</p>
        </div>
      </section>

      <section className="border-b border-gray-200 bg-white px-6 py-10">
        <div className="mx-auto max-w-4xl grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
          {[["5 Lakh","MSEs to onboard"],["Rs 277 Cr","Scheme budget"],["10 Categories","ONDC retail"],["6 SNPs","Live on ONDC"]].map(([v,l]) => (
            <div key={l}><div className="text-2xl font-bold text-indigo-800">{v}</div><div className="text-sm text-gray-500">{l}</div></div>
          ))}
        </div>
      </section>

      <section className="px-6 py-16 bg-gray-50">
        <div className="mx-auto max-w-5xl">
          <h2 className="text-center text-2xl font-bold text-gray-900 mb-2">How VyapaarSetu Works</h2>
          <p className="text-center text-gray-500 mb-10">3 AI-powered steps to get your business on ONDC</p>
          <div className="grid md:grid-cols-3 gap-6">
            {[
              { icon: Mic, step: "Step 1", title: "Voice-Enabled Registration", desc: "Enter Udyam number - AI auto-fills your business details. Speak in Hindi or English." },
              { icon: Tag, step: "Step 2", title: "AI Product Cataloguing", desc: "Describe products in any language. AI maps to ONDC categories and checks compliance." },
              { icon: Users, step: "Step 3", title: "Smart SNP Matching", desc: "AI recommends the best platform for your products and location. Go live in days." },
            ].map(({ icon: Icon, step, title, desc }) => (
              <div key={step} className="rounded-xl bg-white p-6 shadow-sm border border-gray-200">
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-100">
                  <Icon className="h-6 w-6 text-indigo-800" />
                </div>
                <div className="text-sm font-semibold text-yellow-600 mb-1">{step}</div>
                <h3 className="font-semibold text-gray-900 mb-2">{title}</h3>
                <p className="text-sm text-gray-600">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="px-6 py-16 bg-white">
        <div className="mx-auto max-w-4xl">
          <div className="rounded-2xl bg-indigo-50 border border-indigo-100 p-8 flex items-start gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-800 text-white shrink-0">
              <Building2 className="h-6 w-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900 mb-2">TEAM Initiative — Ministry of MSME</h2>
              <p className="text-gray-600 mb-4">Trade Enablement and Marketing scheme provides free ONDC onboarding for eligible MSEs. Government pays platform fees — you pay nothing.</p>
              <div className="grid sm:grid-cols-2 gap-3">
                {["Valid Udyam Registration required","Manufacturing or Services activity","Not already on ONDC","Free — government pays SNP"].map((item) => (
                  <div key={item} className="flex items-center gap-2 text-sm text-gray-700">
                    <CheckCircle className="h-4 w-4 text-green-500 shrink-0" />{item}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="bg-indigo-800 px-6 py-16 text-white text-center">
        <h2 className="text-2xl font-bold mb-3">&#x0905;&#x092D;&#x0940; &#x0936;&#x0941;&#x0930;&#x0942; &#x0915;&#x0930;&#x0947;&#x0902; — Start Today</h2>
        <Link href="/login" className="inline-flex items-center gap-2 rounded-xl bg-yellow-500 px-8 py-3 font-semibold text-white hover:bg-yellow-400">
          Register Free Now <ArrowRight className="h-4 w-4" />
        </Link>
      </section>

      <footer className="border-t border-gray-200 bg-white px-6 py-6 text-center text-sm text-gray-400">
        VyapaarSetu — IndiaAI Innovation Challenge 2026 | Ministry of MSME PS2
      </footer>
    </div>
  );
}
