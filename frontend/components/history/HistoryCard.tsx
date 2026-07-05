"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Diamond, Grid3x3, RefreshCw, Triangle } from "lucide-react";
import { Card } from "@/components/common/Card";
import { ScoreBadge } from "@/components/common/ScoreBadge";
import { useToast } from "@/components/common/Toast";
import { PROVIDER_LABEL } from "@/lib/constants";
import { formatDateTime } from "@/lib/formatters";
import { api, ApiError } from "@/lib/api";
import type { HistoryItem } from "@/lib/types";

const PROVIDER_ICON = { gpt: Grid3x3, claude: Triangle, gemini: Diamond } as const;

export function HistoryCard({ item }: { item: HistoryItem }) {
  const router = useRouter();
  const { showToast } = useToast();
  const [reanalyzing, setReanalyzing] = useState(false);
  const resultHref =
    item.status === "completed"
      ? `/result?question_id=${item.question_id}&tab=summary`
      : `/analyze?question_id=${item.question_id}`;

  async function handleReanalyze() {
    setReanalyzing(true);
    try {
      const res = await api.reanalyze(item.question_id);
      router.push(`/analyze?question_id=${res.question_id}`);
    } catch (err) {
      showToast(err instanceof ApiError ? err.message : "재분석 요청에 실패했습니다.");
      setReanalyzing(false);
    }
  }

  return (
    <Card className="p-5 sm:p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 flex-1">
          <p className="text-base font-semibold text-slate-900">{item.question}</p>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            {item.providers.map((p, idx) => {
              const Icon = PROVIDER_ICON[p];
              return (
                <span
                  key={p}
                  className="flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600"
                >
                  <Icon className="h-3 w-3" aria-hidden="true" />
                  {item.model_names[idx] ?? PROVIDER_LABEL[p]}
                </span>
              );
            })}
          </div>
          <p className="mt-2 text-sm text-slate-500">{item.summary}</p>
          {item.tags.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {item.tags.map((tag) => (
                <span key={tag} className="rounded-md bg-teal-50 px-2 py-0.5 text-xs font-medium text-teal-700">
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>

        <div className="flex shrink-0 flex-row items-center justify-between gap-3 sm:flex-col sm:items-end">
          <div className="text-right">
            {item.trust_score !== null && item.grade ? (
              <>
                <p className="text-2xl font-bold text-slate-900">
                  {item.trust_score}
                  <span className="ml-0.5 text-sm font-normal text-slate-400">/100</span>
                </p>
                <ScoreBadge score={item.trust_score} className="mt-1" />
              </>
            ) : (
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-500">
                진행 중
              </span>
            )}
          </div>
          <p className="text-xs text-slate-400">{formatDateTime(item.created_at)}</p>
          <div className="flex items-center gap-2">
            {item.status === "completed" && (
              <button
                type="button"
                onClick={handleReanalyze}
                disabled={reanalyzing}
                aria-label="재분석"
                className="flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-3.5 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
              >
                <RefreshCw className={`h-3.5 w-3.5 ${reanalyzing ? "animate-spin" : ""}`} aria-hidden="true" />
                재분석
              </button>
            )}
            <Link
              href={resultHref}
              className="flex items-center gap-1 rounded-lg bg-teal-700 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-800"
            >
              결과 보기 &gt;
            </Link>
          </div>
        </div>
      </div>
    </Card>
  );
}
