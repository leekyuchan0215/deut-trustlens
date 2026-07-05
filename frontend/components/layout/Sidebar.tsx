"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Clock, Crown, FileText, LayoutGrid, Plus, Settings, Star } from "lucide-react";
import { Logo } from "@/components/common/Logo";
import { useToast } from "@/components/common/Toast";
import { NOT_READY_MESSAGE, SIDEBAR_ITEMS } from "@/lib/constants";

const ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  home: Plus,
  dashboard: LayoutGrid,
  history: Clock,
  favorites: Star,
  reports: FileText,
  settings: Settings,
};

function isActive(pathname: string, itemKey: string): boolean {
  if (itemKey === "home") return pathname === "/";
  if (itemKey === "dashboard") return pathname.startsWith("/analyze");
  if (itemKey === "history") return pathname.startsWith("/history") || pathname.startsWith("/result");
  return false;
}

export function Sidebar() {
  const pathname = usePathname();
  const { showToast } = useToast();

  return (
    <aside className="flex h-full w-64 shrink-0 flex-col justify-between border-r border-slate-200/70 bg-white/80 px-4 py-6 backdrop-blur-sm">
      <div>
        <div className="mb-8 px-2">
          <Logo />
        </div>
        <nav className="flex flex-col gap-1" aria-label="주요 메뉴">
          {SIDEBAR_ITEMS.map((item) => {
            const Icon = ICONS[item.key];
            const active = isActive(pathname, item.key);
            if (!item.implemented) {
              return (
                <button
                  key={item.key}
                  type="button"
                  onClick={() => showToast(NOT_READY_MESSAGE)}
                  className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm font-medium text-slate-500 transition-colors hover:bg-slate-50"
                >
                  <Icon className="h-4.5 w-4.5" aria-hidden="true" />
                  {item.label}
                </button>
              );
            }
            return (
              <Link
                key={item.key}
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors ${
                  active
                    ? "bg-teal-50 text-teal-700"
                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                }`}
              >
                <Icon className="h-4.5 w-4.5" aria-hidden="true" />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="space-y-4">
        <div className="rounded-2xl bg-slate-900 p-4 text-white">
          <div className="mb-2 flex items-center gap-1.5 text-amber-400">
            <Crown className="h-4 w-4" aria-hidden="true" />
            <span className="text-sm font-semibold">Pro 요금제</span>
          </div>
          <p className="mb-3 text-xs leading-relaxed text-slate-300">
            더 많은 AI 모델과 고급 기능을 사용해보세요.
          </p>
          <button
            type="button"
            onClick={() => showToast(NOT_READY_MESSAGE)}
            className="w-full rounded-lg bg-amber-500 py-2 text-sm font-semibold text-slate-900 transition-colors hover:bg-amber-400"
          >
            업그레이드
          </button>
        </div>
        <button
          type="button"
          onClick={() => showToast(NOT_READY_MESSAGE)}
          aria-label="사용자 계정 메뉴"
          className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-900 text-sm font-semibold text-white"
        >
          N
        </button>
      </div>
    </aside>
  );
}
