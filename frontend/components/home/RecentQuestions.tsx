"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Card } from "@/components/common/Card";
import { ScoreBadge } from "@/components/common/ScoreBadge";
import { EmptyState, ErrorState, LoadingState } from "@/components/common/States";
import { api, ApiError } from "@/lib/api";
import { formatDate } from "@/lib/formatters";
import type { HistoryItem } from "@/lib/types";

export function RecentQuestions() {
  const [items, setItems] = useState<HistoryItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    api
      .history({ sort: "newest", limit: 3 })
      .then((res) => {
        if (cancelled) return;
        setItems(res.items);
        setError(null);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err instanceof ApiError ? err.message : "최근 질문을 불러오지 못했습니다.");
      });
    return () => {
      cancelled = true;
    };
  }, [reloadKey]);

  return (
    <Card className="p-6">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-base font-bold text-slate-900">최근 질문</h2>
        <Link href="/history" className="text-sm font-medium text-teal-700 hover:underline">
          전체 보기 &gt;
        </Link>
      </div>

      {items === null && !error && <LoadingState label="최근 질문을 불러오는 중입니다..." />}
      {error && <ErrorState message={error} onRetry={() => setReloadKey((k) => k + 1)} />}
      {items && items.length === 0 && <EmptyState message="아직 검증한 질문이 없습니다." />}

      {items && items.length > 0 && (
        <ul className="divide-y divide-slate-100">
          {items.map((item) => (
            <li key={item.question_id} className="flex items-center justify-between gap-4 py-3">
              <Link
                href={`/result?question_id=${item.question_id}&tab=summary`}
                className="min-w-0 flex-1 truncate text-sm font-medium text-slate-700 hover:text-teal-700"
              >
                {item.question}
              </Link>
              <div className="flex shrink-0 items-center gap-3">
                {item.trust_score !== null ? (
                  <ScoreBadge score={item.trust_score} />
                ) : (
                  <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-500">
                    진행 중
                  </span>
                )}
                <span className="text-xs text-slate-400">{formatDate(item.created_at)}</span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
