"use client";

import { useRouter } from "next/navigation";
import { clsx } from "clsx";
import { RESULT_TAB_OPTIONS } from "@/lib/constants";
import type { ResultTab } from "@/lib/types";

export function ResultTabs({ questionId, activeTab }: { questionId: string; activeTab: ResultTab }) {
  const router = useRouter();

  return (
    <div className="scrollbar-thin -mx-1 overflow-x-auto border-b border-slate-200">
      <nav className="flex min-w-max gap-1 px-1" aria-label="결과 상세 탭">
        {RESULT_TAB_OPTIONS.map((tab) => {
          const active = tab.value === activeTab;
          return (
            <button
              key={tab.value}
              type="button"
              role="tab"
              aria-selected={active}
              onClick={() =>
                router.replace(`/result?question_id=${questionId}&tab=${tab.value}`, { scroll: false })
              }
              className={clsx(
                "whitespace-nowrap border-b-2 px-4 py-3 text-sm transition-colors",
                active
                  ? "border-teal-600 font-bold text-teal-700"
                  : "border-transparent font-medium text-slate-500 hover:text-slate-800",
              )}
            >
              {tab.label}
            </button>
          );
        })}
      </nav>
    </div>
  );
}
