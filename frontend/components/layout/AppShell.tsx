"use client";

import { useEffect, useState } from "react";
import { X } from "lucide-react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header, type BreadcrumbItem } from "@/components/layout/Header";
import { MOCK_BANNER_MESSAGE } from "@/lib/constants";
import { USE_MOCK } from "@/lib/api";

export function AppShell({
  breadcrumbs,
  children,
}: {
  breadcrumbs: BreadcrumbItem[];
  children: React.ReactNode;
}) {
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    if (!mobileOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setMobileOpen(false);
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [mobileOpen]);

  return (
    <div className="app-gradient-bg flex min-h-screen w-full">
      <div className="hidden md:flex">
        <Sidebar />
      </div>

      {mobileOpen && (
        <div className="fixed inset-0 z-50 flex md:hidden">
          <div
            className="absolute inset-0 bg-slate-900/40"
            onClick={() => setMobileOpen(false)}
            aria-hidden="true"
          />
          <div className="relative z-10 h-full">
            <Sidebar />
          </div>
          <button
            type="button"
            onClick={() => setMobileOpen(false)}
            aria-label="메뉴 닫기"
            className="absolute right-4 top-4 z-20 rounded-full bg-white/90 p-2 text-slate-600 shadow"
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>
      )}

      <div className="flex min-h-screen min-w-0 flex-1 flex-col">
        <Header breadcrumbs={breadcrumbs} onMenuClick={() => setMobileOpen(true)} />
        {USE_MOCK && (
          <div className="border-b border-amber-200/70 bg-amber-50/80 px-4 py-1.5 text-center text-xs font-medium text-amber-800 sm:px-8">
            {MOCK_BANNER_MESSAGE}
          </div>
        )}
        <main className="flex-1 px-4 py-6 sm:px-8 sm:py-8">{children}</main>
      </div>
    </div>
  );
}
