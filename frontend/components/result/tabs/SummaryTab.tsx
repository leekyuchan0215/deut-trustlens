import { AlertCircle, BookMarked, CheckCircle2, Diamond, Grid3x3, ListChecks, Triangle } from "lucide-react";
import { Card } from "@/components/common/Card";
import { TrustScoreGauge } from "@/components/result/TrustScoreGauge";
import { ScoreBreakdownList } from "@/components/result/ScoreBreakdownList";
import { formatDateTime, scoreBadgeClasses } from "@/lib/formatters";
import type { ResultSummaryResponse } from "@/lib/types";

const PROVIDER_ICON = { gpt: Grid3x3, claude: Triangle, gemini: Diamond } as const;

function SummaryInfoCard({
  icon,
  iconClassName,
  title,
  items,
  emptyText,
}: {
  icon: React.ReactNode;
  iconClassName: string;
  title: string;
  items: string[];
  emptyText: string;
}) {
  return (
    <Card className="p-5">
      <div className="mb-3 flex items-center gap-2">
        <span className={`flex h-6 w-6 items-center justify-center rounded-full ${iconClassName}`}>
          {icon}
        </span>
        <h3 className="text-sm font-bold text-slate-900">{title}</h3>
      </div>
      {items.length === 0 ? (
        <p className="text-xs text-slate-400">{emptyText}</p>
      ) : (
        <ul className="space-y-1.5">
          {items.map((item, i) => (
            <li key={i} className="text-xs leading-relaxed text-slate-600">
              &middot; {item}
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

export function SummaryTab({
  summary,
  onViewDetail,
}: {
  summary: ResultSummaryResponse;
  onViewDetail: () => void;
}) {
  const b = summary.trust_score_breakdown;
  const cs = summary.claim_summary;
  const ss = summary.source_summary;

  const verificationItems = [
    cs.verified > 0 ? `${cs.verified}개 검증 완료` : null,
    cs.weak_evidence > 0 ? `${cs.weak_evidence}개 부분 증거` : null,
    cs.unsupported > 0 ? `${cs.unsupported}개 지원 안됨` : null,
    cs.contradicted > 0 ? `${cs.contradicted}개 반박 증거` : null,
  ].filter((x): x is string => x !== null);

  const sourceItems = [
    ss.web_documents > 0 ? `웹 문서 ${ss.web_documents}개` : null,
    ss.academic_papers > 0 ? `학술 논문 ${ss.academic_papers}개` : null,
    ss.technical_blogs > 0 ? `기술 블로그 ${ss.technical_blogs}개` : null,
    ss.official_documents > 0 ? `공식 문서 ${ss.official_documents}개` : null,
    ss.government_sources > 0 ? `정부 자료 ${ss.government_sources}개` : null,
    ss.deterministic_checks > 0 ? `결정적 검증 ${ss.deterministic_checks}건` : null,
  ].filter((x): x is string => x !== null);

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card className="p-6">
          <h2 className="mb-4 text-base font-bold text-slate-900">종합 신뢰도 점수</h2>
          <div className="flex flex-col items-center gap-4 sm:flex-row sm:items-start sm:gap-8">
            <TrustScoreGauge score={b.total_score} grade={b.grade} />
            <div className="w-full flex-1">
              <ScoreBreakdownList breakdown={b} />
            </div>
          </div>
          <p className="mt-3 text-center text-xs text-slate-400 sm:text-left">
            검증 완료: {formatDateTime(summary.completed_at)}
          </p>
        </Card>

        <Card className="p-6">
          <h2 className="mb-4 text-base font-bold text-slate-900">최종 검증 답변</h2>
          <div className="mb-4 rounded-xl bg-teal-50 p-4 text-sm font-medium text-teal-900">
            {summary.summary}
          </div>
          <p className="whitespace-pre-line text-sm leading-relaxed text-slate-700">
            {summary.final_answer}
          </p>
          {summary.cautions.length > 0 && (
            <div className="mt-4 border-t border-slate-100 pt-3">
              <p className="mb-1.5 text-xs font-semibold text-slate-500">주의사항</p>
              <ul className="space-y-1">
                {summary.cautions.map((c, i) => (
                  <li key={i} className="text-xs text-amber-700">
                    &middot; {c}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <SummaryInfoCard
          icon={<ListChecks className="h-3.5 w-3.5 text-white" aria-hidden="true" />}
          iconClassName="bg-indigo-500"
          title="주요 쟁점"
          items={summary.key_issues}
          emptyText="주요 쟁점이 없습니다."
        />
        <SummaryInfoCard
          icon={<CheckCircle2 className="h-3.5 w-3.5 text-white" aria-hidden="true" />}
          iconClassName="bg-emerald-500"
          title="검증 결과"
          items={verificationItems}
          emptyText="검증 결과가 없습니다."
        />
        <SummaryInfoCard
          icon={<AlertCircle className="h-3.5 w-3.5 text-white" aria-hidden="true" />}
          iconClassName="bg-amber-500"
          title="주의사항"
          items={summary.cautions}
          emptyText="주의사항이 없습니다."
        />
        <SummaryInfoCard
          icon={<BookMarked className="h-3.5 w-3.5 text-white" aria-hidden="true" />}
          iconClassName="bg-sky-500"
          title="주요 출처"
          items={sourceItems}
          emptyText="사용된 출처가 없습니다."
        />
      </div>

      <div>
        <h2 className="mb-3 text-base font-bold text-slate-900">AI 모델별 신뢰도</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          {summary.model_scores.map((ms) => {
            const Icon = PROVIDER_ICON[ms.provider];
            return (
              <Card key={ms.provider} className="p-5">
                <div className="mb-2 flex items-center gap-2">
                  <span className="flex h-7 w-7 items-center justify-center rounded-full bg-slate-100 text-slate-600">
                    <Icon className="h-4 w-4" aria-hidden="true" />
                  </span>
                  <span className="text-sm font-semibold text-slate-900">{ms.model_name}</span>
                </div>
                <div className="mb-2 flex items-baseline gap-2">
                  <span className="text-2xl font-bold text-slate-900">{ms.score}</span>
                  <span className="text-xs text-slate-400">/100</span>
                  <span
                    className={`ml-auto rounded-full px-2 py-0.5 text-xs font-medium ${scoreBadgeClasses(ms.score)}`}
                  >
                    {ms.grade}
                  </span>
                </div>
                <p className="text-xs leading-relaxed text-slate-500">{ms.reason}</p>
              </Card>
            );
          })}
        </div>
      </div>

      <button
        type="button"
        onClick={onViewDetail}
        className="flex items-center justify-center gap-2 rounded-xl bg-indigo-600 py-3.5 text-sm font-semibold text-white transition-colors hover:bg-indigo-700"
      >
        상세 분석 보기 →
      </button>
    </div>
  );
}
