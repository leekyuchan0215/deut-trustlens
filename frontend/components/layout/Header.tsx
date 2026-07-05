"use client";

import Link from "next/link";
import { Bell, ChevronDown, Menu, User } from "lucide-react";
import { useToast } from "@/components/common/Toast";
import { NOT_READY_MESSAGE } from "@/lib/constants";

export interface BreadcrumbItem {
  label: string;
  href?: string;
}

export function Header({
  breadcrumbs,
  onMenuClick,
}: {
  breadcrumbs: BreadcrumbItem[];
  onMenuClick?: () => void;
}) {
  const { showToast } = useToast();

  return (
    <header className="flex items-center justify-between border-b border-slate-200/70 bg-white/60 px-4 py-3.5 backdrop-blur-sm sm:px-8">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onMenuClick}
          aria-label="메뉴 열기"
          className="rounded-lg p-1.5 text-slate-600 hover:bg-slate-100 md:hidden"
        >
          <Menu className="h-5 w-5" aria-hidden="true" />
        </button>
        <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-sm text-slate-500">
          {breadcrumbs.map((item, idx) => (
            <span key={idx} className="flex items-center gap-1.5">
              {idx > 0 && <span className="text-slate-300">/</span>}
              {item.href ? (
                <Link href={item.href} className="hover:text-slate-700">
                  {item.label}
                </Link>
              ) : (
                <span className={idx === breadcrumbs.length - 1 ? "text-slate-700" : ""}>
                  {item.label}
                </span>
              )}
            </span>
          ))}
        </nav>
      </div>

      <div className="flex items-center gap-3 sm:gap-4">
        <button
          type="button"
          onClick={() => showToast(NOT_READY_MESSAGE)}
          aria-label="알림"
          className="rounded-full p-2 text-slate-500 hover:bg-slate-100"
        >
          <Bell className="h-4.5 w-4.5" aria-hidden="true" />
        </button>
        <button
          type="button"
          onClick={() => showToast(NOT_READY_MESSAGE)}
          className="flex items-center gap-2 rounded-full py-1 pl-1 pr-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
        >
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-teal-100 text-teal-700">
            <User className="h-4 w-4" aria-hidden="true" />
          </span>
          <span className="hidden sm:inline">사용자</span>
          <ChevronDown className="h-3.5 w-3.5 text-slate-400" aria-hidden="true" />
        </button>
      </div>
    </header>
  );
}
