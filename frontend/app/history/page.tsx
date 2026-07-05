"use client";

import { useEffect, useState } from "react";
import { Search } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { EmptyState, ErrorState, LoadingState } from "@/components/common/States";
import { HistoryCard } from "@/components/history/HistoryCard";
import { api, ApiError } from "@/lib/api";
import {
  HISTORY_PROVIDER_FILTER_OPTIONS,
  HISTORY_SCORE_FILTER_OPTIONS,
  HISTORY_SORT_OPTIONS,
} from "@/lib/constants";
import type { HistoryItem, HistorySort, Provider } from "@/lib/types";

export default function HistoryPage() {
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [scoreFilter, setScoreFilter] = useState("all");
  const [providerFilter, setProviderFilter] = useState("all");
  const [sort, setSort] = useState<HistorySort>("newest");

  const [items, setItems] = useState<HistoryItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const timer = setTimeout(() => setSearch(searchInput.trim()), 300);
    return () => clearTimeout(timer);
  }, [searchInput]);

  useEffect(() => {
    let cancelled = false;
    const scoreOption = HISTORY_SCORE_FILTER_OPTIONS.find((o) => o.value === scoreFilter);

    api
      .history({
        search: search || undefined,
        provider: providerFilter === "all" ? undefined : (providerFilter as Provider),
        min_score: scoreOption?.min,
        max_score: scoreOption?.max,
        sort,
        limit: 50,
      })
      .then((res) => {
        if (cancelled) return;
        setItems(res.items);
        setError(null);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err instanceof ApiError ? err.message : "검증 기록을 불러오지 못했습니다.");
      });

    return () => {
      cancelled = true;
    };
  }, [search, scoreFilter, providerFilter, sort]);

  return (
    <AppShell breadcrumbs={[{ label: "History", href: "/history" }, { label: "검증 기록" }]}>
      <div className="mx-auto flex max-w-5xl flex-col gap-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 sm:text-3xl">검증 기록</h1>
          <p className="mt-1 text-sm text-slate-500">
            이전 질문과 검증 결과를 확인하고 다시 검토할 수 있습니다.
          </p>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row">
          <label className="relative flex-1">
            <span className="sr-only">질문 또는 키워드 검색</span>
            <Search
              className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
              aria-hidden="true"
            />
            <input
              type="search"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="질문 또는 키워드 검색"
              className="w-full rounded-xl border border-slate-200 bg-white py-2.5 pl-10 pr-4 text-sm text-slate-800 outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500"
            />
          </label>

          <label className="sm:w-40">
            <span className="sr-only">점수 필터</span>
            <select
              value={scoreFilter}
              onChange={(e) => setScoreFilter(e.target.value)}
              className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-700 outline-none focus:border-teal-500"
            >
              {HISTORY_SCORE_FILTER_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>

          <label className="sm:w-40">
            <span className="sr-only">모델 필터</span>
            <select
              value={providerFilter}
              onChange={(e) => setProviderFilter(e.target.value)}
              className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-700 outline-none focus:border-teal-500"
            >
              {HISTORY_PROVIDER_FILTER_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>

          <label className="sm:w-36">
            <span className="sr-only">정렬</span>
            <select
              value={sort}
              onChange={(e) => setSort(e.target.value as HistorySort)}
              className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-700 outline-none focus:border-teal-500"
            >
              {HISTORY_SORT_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>
        </div>

        {items === null && !error && <LoadingState label="검증 기록을 불러오는 중입니다..." />}
        {error && <ErrorState message={error} />}
        {items && items.length === 0 && <EmptyState message="조건에 맞는 검증 기록이 없습니다." />}

        {items && items.length > 0 && (
          <div className="flex flex-col gap-4">
            {items.map((item) => (
              <HistoryCard key={item.question_id} item={item} />
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}
