import { Diamond, Grid3x3, Triangle } from "lucide-react";
import { Card } from "@/components/common/Card";
import { PROVIDER_LABEL } from "@/lib/constants";
import type { AiResponse, CrossReview, Provider } from "@/lib/types";

const PROVIDER_ICON = { gpt: Grid3x3, claude: Triangle, gemini: Diamond } as const;

function CrossReviewCard({
  title,
  items,
  tone,
}: {
  title: string;
  items: string[];
  tone: "positive" | "negative" | "neutral" | "warning";
}) {
  const toneClasses = {
    positive: "bg-emerald-50 text-emerald-800",
    negative: "bg-red-50 text-red-800",
    neutral: "bg-slate-50 text-slate-700",
    warning: "bg-amber-50 text-amber-800",
  }[tone];

  return (
    <div className={`rounded-2xl p-5 ${toneClasses}`}>
      <p className="mb-2 text-sm font-bold">
        {title} ({items.length})
      </p>
      {items.length === 0 ? (
        <p className="text-xs opacity-70">항목 없음</p>
      ) : (
        <ul className="space-y-1.5">
          {items.map((item, i) => (
            <li key={i} className="text-xs leading-relaxed">
              &middot; {item}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function AiResponsesTab({
  aiResponses,
  crossReview,
}: {
  aiResponses: AiResponse[];
  crossReview: CrossReview;
}) {
  const missingDescriptions = crossReview.missing_points.map((m) => m.description);

  const additionsByProvider = (provider: Provider) => crossReview.model_additions[provider] ?? [];

  return (
    <div className="flex flex-col gap-6">
      <Card className="p-6">
        <h2 className="mb-4 text-base font-bold text-slate-900">AI 모델별 신뢰도</h2>
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          {aiResponses.map((response) => {
            const Icon = PROVIDER_ICON[response.provider];
            const additions = additionsByProvider(response.provider);
            return (
              <div key={response.id} className="flex flex-col rounded-xl border border-slate-100">
                <div className="flex items-center gap-2 border-b border-slate-100 px-4 py-3">
                  <span className="flex h-7 w-7 items-center justify-center rounded-full bg-slate-100 text-slate-600">
                    <Icon className="h-4 w-4" aria-hidden="true" />
                  </span>
                  <div>
                    <p className="text-sm font-semibold text-slate-900">{response.model_name}</p>
                    <p className="text-xs text-slate-400">{PROVIDER_LABEL[response.provider]}</p>
                  </div>
                </div>
                <div className="scrollbar-thin max-h-64 overflow-y-auto whitespace-pre-line px-4 py-3 text-xs leading-relaxed text-slate-600">
                  {response.status === "failed" ? (
                    <p className="text-red-500">{response.error_message ?? "응답 생성에 실패했습니다."}</p>
                  ) : (
                    response.response_text
                  )}
                </div>
                {additions.length > 0 && (
                  <div className="border-t border-slate-100 px-4 py-2.5">
                    <p className="mb-1 text-[11px] font-semibold text-slate-400">모델 추가 설명</p>
                    <ul className="space-y-1">
                      {additions.map((a, i) => (
                        <li key={i} className="text-[11px] text-slate-500">
                          &middot; {a}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </Card>

      <div>
        <h2 className="mb-1 text-base font-bold text-slate-900">Cross Review 요약</h2>
        <p className="mb-3 text-xs text-slate-400">Judge Agent가 세 모델 답변을 비교한 결과입니다.</p>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <CrossReviewCard title="일치한 내용" items={crossReview.consensus} tone="positive" />
          <CrossReviewCard title="상충한 내용" items={crossReview.contradictions} tone="negative" />
          <CrossReviewCard title="누락된 내용" items={missingDescriptions} tone="neutral" />
          <CrossReviewCard title="과도한 주장" items={crossReview.overclaims} tone="warning" />
        </div>
      </div>
    </div>
  );
}
