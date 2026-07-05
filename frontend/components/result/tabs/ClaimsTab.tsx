"use client";

import { useState } from "react";
import { Card } from "@/components/common/Card";
import { EmptyState } from "@/components/common/States";
import { consensusLevelLabel, riskLevelClasses, riskLevelLabel, verificationStatusClasses } from "@/lib/formatters";
import { VERIFICATION_STATUS_LABEL } from "@/lib/constants";
import type { Claim, VerificationStatus } from "@/lib/types";

const FILTERS: { value: VerificationStatus | "all"; label: string }[] = [
  { value: "all", label: "전체" },
  { value: "verified", label: "검증 완료" },
  { value: "weak_evidence", label: "부분 증거" },
  { value: "contradicted", label: "반박 증거" },
  { value: "unsupported", label: "지원 안됨" },
];

const LEGEND: { status: VerificationStatus; text: string }[] = [
  { status: "verified", text: "Verified: 충분한 근거로 뒷받침됨" },
  { status: "weak_evidence", text: "Weak Evidence: 근거가 부족하거나 제한적" },
  { status: "contradicted", text: "Contradicted: 근거에 의해 반박됨" },
  { status: "unsupported", text: "Unsupported: 근거 부족" },
];

export function ClaimsTab({ claims }: { claims: Claim[] }) {
  const [filter, setFilter] = useState<VerificationStatus | "all">("all");
  const filtered = filter === "all" ? claims : claims.filter((c) => c.verification_status === filter);

  return (
    <Card className="p-6">
      <h2 className="text-base font-bold text-slate-900">주장 검증 결과</h2>
      <p className="mb-4 text-xs text-slate-400">
        AI 답변을 구성하는 주요 주장을 분해하고 각 주장의 사실 여부를 평가했습니다.
      </p>

      <div className="mb-4 flex flex-wrap gap-2" role="group" aria-label="검증 결과 필터">
        {FILTERS.map((f) => {
          const count = f.value === "all" ? claims.length : claims.filter((c) => c.verification_status === f.value).length;
          const active = filter === f.value;
          return (
            <button
              key={f.value}
              type="button"
              aria-pressed={active}
              onClick={() => setFilter(f.value)}
              className={`rounded-lg px-3.5 py-2 text-sm font-medium transition-colors ${
                active ? "bg-teal-700 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              {f.label} {f.value === "all" ? count : count}
            </button>
          );
        })}
      </div>

      {filtered.length === 0 ? (
        <EmptyState message="해당하는 주장이 없습니다." />
      ) : (
        <>
          <div className="scrollbar-thin hidden overflow-x-auto sm:block">
            <table className="w-full min-w-[640px] text-left text-sm">
              <thead>
                <tr className="border-b border-slate-100 text-xs font-semibold text-slate-400">
                  <th className="py-2 pr-3 font-semibold">Claim ID</th>
                  <th className="py-2 pr-3 font-semibold">주장 내용</th>
                  <th className="py-2 pr-3 font-semibold">AI 합의도</th>
                  <th className="py-2 pr-3 font-semibold">검증 결과</th>
                  <th className="py-2 pr-3 font-semibold">근거 수</th>
                  <th className="py-2 pr-3 font-semibold">위험도</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((claim) => (
                  <tr key={claim.id} className="border-b border-slate-50 align-top">
                    <td className="py-3 pr-3 font-semibold text-slate-500">{claim.display_id}</td>
                    <td className="max-w-xs py-3 pr-3 text-slate-800">{claim.claim_text}</td>
                    <td className="py-3 pr-3">
                      <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">
                        {consensusLevelLabel(claim.consensus_level)}
                      </span>
                    </td>
                    <td className="py-3 pr-3">
                      <span
                        className={`rounded-full px-2.5 py-1 text-xs font-semibold ${verificationStatusClasses(claim.verification_status)}`}
                      >
                        {VERIFICATION_STATUS_LABEL[claim.verification_status]}
                      </span>
                    </td>
                    <td className="py-3 pr-3 text-slate-600">{claim.evidence_count}</td>
                    <td className="py-3 pr-3">
                      <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${riskLevelClasses(claim.risk_level)}`}>
                        {riskLevelLabel(claim.risk_level)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <ul className="flex flex-col gap-3 sm:hidden">
            {filtered.map((claim) => (
              <li key={claim.id} className="rounded-xl border border-slate-100 p-4">
                <div className="mb-1.5 flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-400">{claim.display_id}</span>
                  <span
                    className={`rounded-full px-2.5 py-1 text-xs font-semibold ${verificationStatusClasses(claim.verification_status)}`}
                  >
                    {VERIFICATION_STATUS_LABEL[claim.verification_status]}
                  </span>
                </div>
                <p className="mb-2 text-sm text-slate-800">{claim.claim_text}</p>
                <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500">
                  <span>AI 합의도: {consensusLevelLabel(claim.consensus_level)}</span>
                  <span>근거 수: {claim.evidence_count}</span>
                  <span className={`rounded-full px-2 py-0.5 font-medium ${riskLevelClasses(claim.risk_level)}`}>
                    위험도 {riskLevelLabel(claim.risk_level)}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        </>
      )}

      <div className="mt-4 flex flex-wrap gap-x-6 gap-y-1.5 border-t border-slate-100 pt-4 text-xs text-slate-500">
        {LEGEND.map((l) => (
          <span key={l.status} className="flex items-center gap-1.5">
            <span className={`h-2.5 w-2.5 rounded-full ${verificationStatusClasses(l.status).split(" ")[0]}`} aria-hidden="true" />
            {l.text}
          </span>
        ))}
      </div>
    </Card>
  );
}
