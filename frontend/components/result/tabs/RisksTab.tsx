"use client";

import { useState } from "react";
import { AlertTriangle, ChevronDown, Clock, Scale, ShieldCheck, Sparkles } from "lucide-react";
import { Card } from "@/components/common/Card";
import { EmptyState } from "@/components/common/States";
import { RISK_TYPE_LABEL } from "@/lib/constants";
import { riskLevelClasses, riskLevelLabel } from "@/lib/formatters";
import type { Claim, ClaimDistribution, Risk, RiskType } from "@/lib/types";

const RISK_ICON: Record<RiskType, React.ComponentType<{ className?: string }>> = {
  hallucination: Sparkles,
  source_credibility: ShieldCheck,
  outdated_information: Clock,
  contradiction: Scale,
};

const RISK_ORDER: RiskType[] = ["hallucination", "source_credibility", "outdated_information", "contradiction"];

function overallLevel(risks: Risk[]): "low" | "medium" | "high" {
  if (risks.some((r) => r.risk_level === "high")) return "high";
  if (risks.some((r) => r.risk_level === "medium")) return "medium";
  return "low";
}

export function RisksTab({
  risks,
  claims,
  claimDistribution,
}: {
  risks: Risk[];
  claims: Claim[];
  claimDistribution: ClaimDistribution;
}) {
  const [openType, setOpenType] = useState<RiskType | null>(RISK_ORDER[0]);

  const findClaimLabel = (claimId: string | null) => {
    if (!claimId) return null;
    return claims.find((c) => c.id === claimId)?.display_id ?? null;
  };

  const totalClaims =
    claimDistribution.verified +
    claimDistribution.weak_evidence +
    claimDistribution.unsupported +
    claimDistribution.contradicted;

  return (
    <Card className="p-6">
      <h2 className="mb-4 text-base font-bold text-slate-900">위험 분석</h2>

      <div className="mb-5 flex items-start gap-2 rounded-xl bg-amber-50 px-4 py-3 text-sm text-amber-800">
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
        <p>
          검증 Claim {totalClaims}개 중 verified {claimDistribution.verified}개, weak{" "}
          {claimDistribution.weak_evidence}개, contradicted {claimDistribution.contradicted}개.
        </p>
      </div>

      <div className="flex flex-col gap-3">
        {RISK_ORDER.map((type) => {
          const typeRisks = risks.filter((r) => r.risk_type === type);
          const Icon = RISK_ICON[type];
          const level = overallLevel(typeRisks);
          const open = openType === type;
          return (
            <div key={type} className="rounded-xl border border-slate-100">
              <button
                type="button"
                aria-expanded={open}
                onClick={() => setOpenType(open ? null : type)}
                className="flex w-full items-center gap-3 px-5 py-4 text-left"
              >
                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-slate-100 text-slate-600">
                  <Icon className="h-4 w-4" aria-hidden="true" />
                </span>
                <span className="flex-1">
                  <span className="flex items-center gap-2">
                    <span className="text-sm font-bold text-slate-900">{RISK_TYPE_LABEL[type]}</span>
                    <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${riskLevelClasses(level)}`}>
                      {riskLevelLabel(level)}
                    </span>
                  </span>
                  <span className="mt-0.5 block text-xs text-slate-400">
                    관련 항목 {typeRisks.length}건
                  </span>
                </span>
                <ChevronDown
                  className={`h-4 w-4 shrink-0 text-slate-400 transition-transform ${open ? "rotate-180" : ""}`}
                  aria-hidden="true"
                />
              </button>
              {open && (
                <div className="border-t border-slate-100 px-5 py-4">
                  {typeRisks.length === 0 ? (
                    <EmptyState message="해당 위험 항목이 없습니다." />
                  ) : (
                    <ul className="flex flex-col gap-3">
                      {typeRisks.map((risk) => {
                        const claimLabel = findClaimLabel(risk.claim_id);
                        return (
                          <li key={risk.id} className="rounded-lg bg-slate-50 p-4 text-sm">
                            <div className="mb-1.5 flex flex-wrap items-center gap-2">
                              <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${riskLevelClasses(risk.risk_level)}`}>
                                {riskLevelLabel(risk.risk_level)}
                              </span>
                              {claimLabel && (
                                <span className="rounded-full bg-slate-200 px-2 py-0.5 text-xs font-medium text-slate-600">
                                  관련 Claim: {claimLabel}
                                </span>
                              )}
                            </div>
                            <p className="mb-2 text-slate-700">{risk.description}</p>
                            <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500">
                              <span>Core 영향: {risk.affects_core_answer ? "예" : "아니오"}</span>
                              <span>Evidence로 해결: {risk.resolved_by_evidence ? "예" : "아니오"}</span>
                              <span className="font-semibold text-slate-700">적용 Penalty: {risk.penalty}</span>
                            </div>
                          </li>
                        );
                      })}
                    </ul>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </Card>
  );
}
