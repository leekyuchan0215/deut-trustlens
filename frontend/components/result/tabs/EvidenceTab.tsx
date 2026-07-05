import { Calculator } from "lucide-react";
import { Card } from "@/components/common/Card";
import { EmptyState } from "@/components/common/States";
import { SafeExternalLink } from "@/components/common/SafeExternalLink";
import { SOURCE_TYPE_LABEL } from "@/lib/constants";
import { formatDate, relevancePercent } from "@/lib/formatters";
import type { DeterministicCheck, Evidence } from "@/lib/types";

function EvidenceCard({ evidence }: { evidence: Evidence }) {
  return (
    <div className="rounded-xl border border-slate-100 p-5">
      <div className="mb-1 flex items-start justify-between gap-3">
        <SafeExternalLink href={evidence.url} className="text-sm font-medium">
          {evidence.domain}
        </SafeExternalLink>
        <span className="shrink-0 rounded-full bg-teal-50 px-2.5 py-1 text-xs font-semibold text-teal-700">
          관련도 {relevancePercent(evidence.hybrid_score)}%
        </span>
      </div>
      <p className="mb-1.5 text-sm font-semibold text-slate-900">{evidence.title}</p>
      <p className="mb-3 text-sm leading-relaxed text-slate-600">{evidence.snippet}</p>
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-400">
        <span>검색일: {formatDate(evidence.searched_at)}</span>
        <span>{SOURCE_TYPE_LABEL[evidence.source_type]}</span>
        <SafeExternalLink href={evidence.url} className="text-teal-700">
          출처 보기
        </SafeExternalLink>
      </div>
    </div>
  );
}

function DeterministicCheckCard({ check }: { check: DeterministicCheck }) {
  return (
    <div className="rounded-xl border border-slate-100 bg-slate-50 p-5">
      <div className="mb-2 flex items-center gap-2 text-slate-700">
        <Calculator className="h-4 w-4" aria-hidden="true" />
        <p className="text-sm font-semibold">결정적 검증 · {check.check_type}</p>
      </div>
      <p className="mb-1 text-sm text-slate-700">
        입력: <span className="font-mono">{check.input_expression}</span>
      </p>
      <p className="mb-1 text-sm text-slate-700">
        기대 결과: <span className="font-mono">{check.expected_result}</span> / AI 답변:{" "}
        <span className="font-mono">{check.ai_claimed_result}</span>
      </p>
      <p className="text-xs text-slate-500">{check.verification_reason}</p>
    </div>
  );
}

export function EvidenceTab({
  evidences,
  deterministicChecks,
}: {
  evidences: Evidence[];
  deterministicChecks: DeterministicCheck[];
}) {
  const sorted = [...evidences].sort((a, b) => a.rank - b.rank);

  return (
    <Card className="p-6">
      <h2 className="text-base font-bold text-slate-900">근거 자료</h2>
      <p className="mb-4 text-xs text-slate-400">Claim 검증에 사용된 주요 Evidence Pack입니다.</p>

      {deterministicChecks.length > 0 && (
        <div className="mb-5 flex flex-col gap-3">
          {deterministicChecks.map((check) => (
            <DeterministicCheckCard key={check.id} check={check} />
          ))}
        </div>
      )}

      {sorted.length === 0 ? (
        deterministicChecks.length === 0 && <EmptyState message="사용된 근거 자료가 없습니다." />
      ) : (
        <div className="flex flex-col gap-3">
          {sorted.map((evidence) => (
            <EvidenceCard key={evidence.id} evidence={evidence} />
          ))}
        </div>
      )}
    </Card>
  );
}
