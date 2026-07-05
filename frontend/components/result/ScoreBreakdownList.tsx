"use client";

import { useState } from "react";
import { ChevronDown } from "lucide-react";
import { VERIFICATION_BASIS_LABEL } from "@/lib/constants";
import type { ScoreReason, TrustScoreBreakdown } from "@/lib/types";

interface Row {
  key: string;
  label: string;
  value: number;
  reason?: ScoreReason;
  isPenalty?: boolean;
}

function Bar({ value, isPenalty }: { value: number; isPenalty?: boolean }) {
  const pct = Math.max(0, Math.min(100, isPenalty ? value : value));
  return (
    <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
      <div
        className={`h-full rounded-full ${isPenalty ? "bg-red-400" : "bg-teal-600"}`}
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

function ExtraEvidenceDetail({ breakdown }: { breakdown: TrustScoreBreakdown }) {
  const d = breakdown.calculation_detail;
  const items: { label: string; value: number }[] = [
    { label: "Core Claim 수", value: d.core_claim_count },
    { label: "검증된 Core Claim 수", value: d.verified_core_claim_count },
    { label: "Weak Core Claim 수", value: d.weak_core_claim_count },
    { label: "Unsupported Core Claim 수", value: d.unsupported_core_claim_count },
    { label: "Contradicted Core Claim 수", value: d.contradicted_core_claim_count },
    { label: "Supporting Claim 수", value: d.supporting_claim_count },
    { label: "사용된 Evidence 수", value: d.used_evidence_count },
    { label: "공식 출처 수", value: d.official_source_count },
    { label: "Deterministic Check 수", value: d.deterministic_check_count },
  ];
  return (
    <dl className="mt-3 grid grid-cols-2 gap-x-4 gap-y-1.5 border-t border-slate-100 pt-3 sm:grid-cols-3">
      {items.map((item) => (
        <div key={item.label} className="flex items-baseline justify-between gap-2 text-xs">
          <dt className="text-slate-400">{item.label}</dt>
          <dd className="font-semibold text-slate-700">{item.value}</dd>
        </div>
      ))}
    </dl>
  );
}

export function ScoreBreakdownList({ breakdown }: { breakdown: TrustScoreBreakdown }) {
  const [openKey, setOpenKey] = useState<string | null>(null);

  const rows: Row[] = [
    {
      key: "evidence_support",
      label: "근거 지지도",
      value: breakdown.evidence_support_score,
      reason: breakdown.score_reasons.evidence_support,
    },
    {
      key: "source_quality",
      label: "출처 품질",
      value: breakdown.source_quality_score,
      reason: breakdown.score_reasons.source_quality,
    },
    {
      key: "consensus",
      label: "AI 합의도",
      value: breakdown.consensus_score,
      reason: breakdown.score_reasons.consensus,
    },
    {
      key: "logic",
      label: "논리적 일관성",
      value: breakdown.logic_score,
      reason: breakdown.score_reasons.logic,
    },
    {
      key: "freshness",
      label: "최신성",
      value: breakdown.freshness_score,
      reason: breakdown.score_reasons.freshness,
    },
    { key: "contradiction_penalty", label: "모순 패널티", value: breakdown.contradiction_penalty, isPenalty: true },
    { key: "risk_penalty", label: "위험 패널티", value: breakdown.risk_penalty, isPenalty: true },
  ];

  return (
    <div className="flex flex-col gap-1">
      {rows.map((row) => {
        const expandable = !row.isPenalty && !!row.reason;
        const open = openKey === row.key;
        return (
          <div key={row.key} className="border-b border-slate-50 last:border-0">
            <button
              type="button"
              disabled={!expandable}
              aria-expanded={expandable ? open : undefined}
              onClick={() => expandable && setOpenKey(open ? null : row.key)}
              className={`flex w-full items-center gap-3 py-2 text-left ${expandable ? "cursor-pointer" : "cursor-default"}`}
            >
              <span className="w-28 shrink-0 text-sm text-slate-600">{row.label}</span>
              <span className="flex-1">
                <Bar value={row.value} isPenalty={row.isPenalty} />
              </span>
              <span className="w-10 shrink-0 text-right text-sm font-semibold text-slate-800">
                {row.value}
              </span>
              {expandable && (
                <ChevronDown
                  className={`h-4 w-4 shrink-0 text-slate-400 transition-transform ${open ? "rotate-180" : ""}`}
                  aria-hidden="true"
                />
              )}
            </button>
            {expandable && open && row.reason && (
              <div className="mb-3 rounded-xl bg-slate-50 p-4 text-sm">
                <p className="text-slate-700">{row.reason.reason}</p>
                <p className="mt-1 text-xs text-slate-400">
                  검증 근거: {VERIFICATION_BASIS_LABEL[row.reason.verification_basis]}
                </p>
                {row.reason.positive_factors.length > 0 && (
                  <ul className="mt-2 space-y-1">
                    {row.reason.positive_factors.map((f, i) => (
                      <li key={i} className="flex gap-1.5 text-emerald-700">
                        <span aria-hidden="true">+</span>
                        <span>{f}</span>
                      </li>
                    ))}
                  </ul>
                )}
                {row.reason.negative_factors.length > 0 && (
                  <ul className="mt-2 space-y-1">
                    {row.reason.negative_factors.map((f, i) => (
                      <li key={i} className="flex gap-1.5 text-red-600">
                        <span aria-hidden="true">-</span>
                        <span>{f}</span>
                      </li>
                    ))}
                  </ul>
                )}
                {row.key === "evidence_support" && <ExtraEvidenceDetail breakdown={breakdown} />}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
