"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { AppShell } from "@/components/layout/AppShell";
import { Card } from "@/components/common/Card";
import { ErrorState, LoadingState } from "@/components/common/States";
import { ResultHeader } from "@/components/result/ResultHeader";
import { ResultTabs } from "@/components/result/ResultTabs";
import { SummaryTab } from "@/components/result/tabs/SummaryTab";
import { AiResponsesTab } from "@/components/result/tabs/AiResponsesTab";
import { ClaimsTab } from "@/components/result/tabs/ClaimsTab";
import { EvidenceTab } from "@/components/result/tabs/EvidenceTab";
import { RisksTab } from "@/components/result/tabs/RisksTab";
import { GraphTab } from "@/components/result/tabs/GraphTab";
import { api, ApiError } from "@/lib/api";
import { DEFAULT_RESULT_TAB, RESULT_TAB_OPTIONS } from "@/lib/constants";
import type { ResultDetailResponse, ResultSummaryResponse, ResultTab } from "@/lib/types";

function isValidTab(value: string | null): value is ResultTab {
  return RESULT_TAB_OPTIONS.some((t) => t.value === value);
}

function ResultContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const questionId = searchParams.get("question_id");
  const rawTab = searchParams.get("tab");
  const tab: ResultTab = isValidTab(rawTab) ? rawTab : DEFAULT_RESULT_TAB;

  const [summary, setSummary] = useState<ResultSummaryResponse | null>(null);
  const [detail, setDetail] = useState<ResultDetailResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);

  useEffect(() => {
    if (!questionId) return;
    let cancelled = false;

    api
      .resultSummary(questionId)
      .then((res) => {
        if (cancelled) return;
        setSummary(res);
        setError(null);
      })
      .catch((err) => {
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 409) {
          router.replace(`/analyze?question_id=${questionId}`);
          return;
        }
        setError(
          err instanceof ApiError ? err.message : "결과를 불러오지 못했습니다. 다시 시도해주세요.",
        );
      });

    api
      .resultDetail(questionId)
      .then((res) => {
        if (cancelled) return;
        setDetail(res);
        setDetailError(null);
      })
      .catch((err) => {
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 409) return;
        setDetailError(
          err instanceof ApiError ? err.message : "상세 결과를 불러오지 못했습니다.",
        );
      });

    return () => {
      cancelled = true;
    };
  }, [questionId, router]);

  const missingIdError = !questionId ? "질문 ID가 없습니다. 홈에서 새로운 질문을 시작해주세요." : null;
  const displayError = missingIdError ?? error;

  if (displayError) {
    return (
      <Card className="p-8">
        <ErrorState message={displayError} />
        <div className="mt-2 text-center">
          <Link href="/history" className="text-sm font-medium text-teal-700 hover:underline">
            검증 기록으로 이동
          </Link>
        </div>
      </Card>
    );
  }

  if (!summary) {
    return (
      <Card className="p-8">
        <LoadingState label="검증 결과를 불러오는 중입니다..." />
      </Card>
    );
  }

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6">
      <ResultHeader
        questionId={summary.question_id}
        selectedQuestion={summary.selected_question}
        originalQuestion={summary.original_question}
        refinedQuestion={summary.refined_question}
        answerPurpose={summary.answer_purpose}
      />
      <ResultTabs questionId={summary.question_id} activeTab={tab} />

      {tab === "summary" && (
        <SummaryTab
          summary={summary}
          onViewDetail={() =>
            router.replace(`/result?question_id=${summary.question_id}&tab=ai-responses`)
          }
        />
      )}

      {tab !== "summary" && detailError && (
        <Card className="p-8">
          <ErrorState message={detailError} />
        </Card>
      )}

      {tab !== "summary" && !detailError && !detail && (
        <Card className="p-8">
          <LoadingState label="상세 결과를 불러오는 중입니다..." />
        </Card>
      )}

      {tab !== "summary" && detail && (
        <>
          {tab === "ai-responses" && (
            <AiResponsesTab aiResponses={detail.ai_responses} crossReview={detail.cross_review} />
          )}
          {tab === "claims" && <ClaimsTab claims={detail.claims} />}
          {tab === "evidence" && (
            <EvidenceTab evidences={detail.evidences} deterministicChecks={detail.deterministic_checks} />
          )}
          {tab === "risks" && (
            <RisksTab
              risks={detail.risk_analysis}
              claims={detail.claims}
              claimDistribution={detail.claim_distribution}
            />
          )}
          {tab === "graph" && (
            <GraphTab
              breakdown={detail.trust_score_breakdown}
              claimDistribution={detail.claim_distribution}
              claimEvidenceRelations={detail.claim_evidence_relations}
              crossReview={detail.cross_review}
            />
          )}
        </>
      )}
    </div>
  );
}

export default function ResultPage() {
  return (
    <AppShell breadcrumbs={[{ label: "Result", href: "/result" }, { label: "검증 결과" }]}>
      <Suspense fallback={<LoadingState label="불러오는 중입니다..." />}>
        <ResultContent />
      </Suspense>
    </AppShell>
  );
}
