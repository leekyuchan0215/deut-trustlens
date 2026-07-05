import { Card } from "@/components/common/Card";
import { VERIFICATION_STATUS_LABEL } from "@/lib/constants";
import { verificationStatusClasses } from "@/lib/formatters";
import type { ClaimDistribution, ClaimEvidenceRelation, CrossReview, TrustScoreBreakdown } from "@/lib/types";

function ScoreBar({ label, value, max = 100 }: { label: string; value: number; max?: number }) {
  const pct = Math.max(0, Math.min(100, (Math.abs(value) / max) * 100));
  return (
    <div className="flex items-center gap-3">
      <span className="w-24 shrink-0 text-sm text-slate-600">{label}</span>
      <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100">
        <div className="h-full rounded-full bg-teal-600" style={{ width: `${pct}%` }} />
      </div>
      <span className="w-10 shrink-0 text-right text-sm font-semibold text-slate-800">{value}</span>
    </div>
  );
}

function DistributionBar({
  label,
  value,
  total,
  colorClassName,
}: {
  label: string;
  value: number;
  total: number;
  colorClassName: string;
}) {
  const pct = total > 0 ? (value / total) * 100 : 0;
  return (
    <div className="flex items-center gap-3">
      <span className="w-20 shrink-0 text-sm text-slate-600">{label}</span>
      <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100">
        <div className={`h-full rounded-full ${colorClassName}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="w-8 shrink-0 text-right text-sm font-semibold text-slate-800">{value}</span>
    </div>
  );
}

function CrossReviewMini({ title, count, tone }: { title: string; count: number; tone: string }) {
  return (
    <div className={`rounded-xl p-4 ${tone}`}>
      <p className="text-xs font-medium opacity-80">{title}</p>
      <p className="text-2xl font-bold">{count}</p>
    </div>
  );
}

export function GraphTab({
  breakdown,
  claimDistribution,
  claimEvidenceRelations,
  crossReview,
}: {
  breakdown: TrustScoreBreakdown;
  claimDistribution: ClaimDistribution;
  claimEvidenceRelations: ClaimEvidenceRelation[];
  crossReview: CrossReview;
}) {
  const totalClaims =
    claimDistribution.verified +
    claimDistribution.weak_evidence +
    claimDistribution.unsupported +
    claimDistribution.contradicted;
  const totalEvidence = claimEvidenceRelations.reduce((sum, r) => sum + r.evidences.length, 0);
  const combinedPenalty = breakdown.contradiction_penalty + breakdown.risk_penalty;

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card className="p-6">
          <h2 className="text-base font-bold text-slate-900">Trust Score 구성</h2>
          <p className="mb-4 text-xs text-slate-400">
            최종 점수 {breakdown.total_score}점 · {breakdown.grade}
          </p>
          <div className="flex flex-col gap-3">
            <ScoreBar label="근거 지지도" value={breakdown.evidence_support_score} />
            <ScoreBar label="출처 품질" value={breakdown.source_quality_score} />
            <ScoreBar label="AI 합의도" value={breakdown.consensus_score} />
            <ScoreBar label="논리 일관성" value={breakdown.logic_score} />
            <ScoreBar label="최신성" value={breakdown.freshness_score} />
            <ScoreBar label="Penalty" value={combinedPenalty} max={70} />
          </div>
        </Card>

        <Card className="p-6">
          <h2 className="mb-4 text-base font-bold text-slate-900">Claim 검증 분포</h2>
          <div className="flex flex-col gap-3">
            <DistributionBar
              label="검증 완료"
              value={claimDistribution.verified}
              total={totalClaims}
              colorClassName="bg-emerald-500"
            />
            <DistributionBar
              label="부분 근거"
              value={claimDistribution.weak_evidence}
              total={totalClaims}
              colorClassName="bg-amber-500"
            />
            <DistributionBar
              label="미지원"
              value={claimDistribution.unsupported}
              total={totalClaims}
              colorClassName="bg-slate-400"
            />
            <DistributionBar
              label="반박됨"
              value={claimDistribution.contradicted}
              total={totalClaims}
              colorClassName="bg-red-500"
            />
          </div>
        </Card>
      </div>

      <Card className="p-6">
        <h2 className="text-base font-bold text-slate-900">Claim &harr; Evidence 관계</h2>
        <p className="mb-4 text-xs text-slate-400">
          검증에 사용된 Claim {claimEvidenceRelations.length}개 · Evidence {totalEvidence}개
        </p>
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <div className="flex flex-col gap-2">
            <p className="text-xs font-semibold text-slate-400">CLAIMS</p>
            {claimEvidenceRelations.map((rel) => (
              <div key={rel.claim_id} className="rounded-lg border border-slate-100 px-3 py-2">
                <p className="text-sm text-slate-800">{rel.claim_text}</p>
                <p className="mt-1 flex items-center gap-2 text-xs">
                  <span className={`rounded-full px-2 py-0.5 font-semibold ${verificationStatusClasses(rel.verification_status)}`}>
                    {VERIFICATION_STATUS_LABEL[rel.verification_status]}
                  </span>
                  <span className="text-slate-400">evidence {rel.evidences.length}개</span>
                </p>
              </div>
            ))}
          </div>
          <div className="flex flex-col gap-2">
            <p className="text-xs font-semibold text-slate-400">EVIDENCE</p>
            {claimEvidenceRelations.flatMap((rel) =>
              rel.evidences.map((e) => (
                <div key={e.evidence_id} className="rounded-lg border border-slate-100 px-3 py-2">
                  <p className="text-sm text-slate-800">{e.title}</p>
                  <p className="text-xs text-teal-700">{e.domain}</p>
                </div>
              )),
            )}
          </div>
        </div>
      </Card>

      <Card className="p-6">
        <h2 className="mb-4 text-base font-bold text-slate-900">Cross Review 요약</h2>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <CrossReviewMini title="일치" count={crossReview.consensus.length} tone="bg-emerald-50 text-emerald-800" />
          <CrossReviewMini title="상충" count={crossReview.contradictions.length} tone="bg-red-50 text-red-800" />
          <CrossReviewMini title="누락" count={crossReview.missing_points.length} tone="bg-slate-100 text-slate-700" />
          <CrossReviewMini title="과잉 주장" count={crossReview.overclaims.length} tone="bg-amber-50 text-amber-800" />
        </div>
      </Card>
    </div>
  );
}
