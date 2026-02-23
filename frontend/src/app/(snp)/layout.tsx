"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuthStore } from "@/store/auth";
import { LayoutDashboard, Users, LogOut } from "lucide-react";

export default function SNPLayout({ children }: { children: React.ReactNode }) {
  const { hydrate, isAuthenticated, logout } = useAuthStore();
  const router = useRouter();

  useEffect(() => { hydrate(); }, [hydrate]);
  useEffect(() => { if (!isAuthenticated) router.push("/login"); }, [isAuthenticated, router]);

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <aside className="w-56 bg-indigo-900 text-white flex flex-col">
        <div className="px-4 py-5 border-b border-indigo-800">
          <div className="font-bold text-lg">VyapaarSetu</div>
          <div className="text-xs text-indigo-300">SNP Portal</div>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1">
          {[
            { href: "/snp/dashboard", icon: LayoutDashboard, label: "Dashboard" },
            { href: "/snp/leads", icon: Users, label: "MSE Leads" },
          ].map(({ href, icon: Icon, label }) => (
            <Link key={href} href={href}
              className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-indigo-200 hover:bg-indigo-800 hover:text-white transition-colors">
              <Icon className="h-4 w-4" />{label}
            </Link>
          ))}
        </nav>
        <div className="px-3 py-4 border-t border-indigo-800">
          <button onClick={() => { logout(); router.push("/login"); }}
            className="flex items-center gap-2 w-full rounded-lg px-3 py-2 text-sm text-indigo-300 hover:bg-indigo-800 hover:text-white">
            <LogOut className="h-4 w-4" />Logout
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  );
}
