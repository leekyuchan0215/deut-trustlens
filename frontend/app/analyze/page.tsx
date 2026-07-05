"use client";

import { Suspense, useEffect } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { AppShell } from "@/components/layout/AppShell";
import { Card } from "@/components/common/Card";
import { ErrorState, LoadingState } from "@/components/common/States";
import { ModelStatusCard } from "@/components/analysis/ModelStatusCard";
import { StageList } from "@/components/analysis/StageList";
import { useAnalysisPolling } from "@/hooks/useAnalysisPolling";
import { DISPLAY_STAGE_LABEL } from "@/lib/constants";

function AnalyzeContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const questionId = searchParams.get("question_id");
  const { progress, error, done } = useAnalysisPolling(questionId);

  useEffect(() => {
    if (progress?.status === "completed" && questionId) {
      router.replace(`/result?question_id=${questionId}&tab=summary`);
    }
  }, [progress?.status, questionId, router]);

  if (error) {
    return (
      <Card className="p-8">
        <ErrorState
          message={error}
          onRetry={done && questionId ? () => router.replace("/") : undefined}
        />
        {!questionId && (
          <div className="mt-2 text-center">
            <Link href="/" className="text-sm font-medium text-teal-700 hover:underline">
              홈으로 돌아가기
            </Link>
          </div>
        )}
      </Card>
    );
  }

  if (!progress) {
    return (
      <Card className="p-8">
        <LoadingState label="검증 작업을 준비하고 있습니다..." />
      </Card>
    );
  }

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-6">
      <div className="text-center sm:text-left">
        <h1 className="text-2xl font-bold text-slate-900 sm:text-3xl">
          TrustLens가 답변을 검증하고 있습니다
        </h1>
        <p className="mt-2 text-sm text-slate-500">
          다중 AI 답변 생성, Claim 검증, 외부 근거 검색을 진행합니다.
        </p>
        <p className="mt-1 text-sm font-semibold text-teal-700">
          현재 단계: {DISPLAY_STAGE_LABEL[progress.display_stage]}
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {progress.model_statuses.map((status) => (
          <ModelStatusCard key={status.provider} status={status} />
        ))}
      </div>

      <Card className="p-6">
        <h2 className="mb-3 text-base font-bold text-slate-900">검증 단계</h2>
        <StageList steps={progress.display_steps} />
      </Card>

      <Card className="p-6">
        <div className="mb-2 flex items-center justify-between">
          <h2 className="text-base font-bold text-slate-900">전체 진행률</h2>
          <span className="text-sm font-semibold text-teal-700">{progress.progress_percent}%</span>
        </div>
        <div
          role="progressbar"
          aria-valuenow={progress.progress_percent}
          aria-valuemin={0}
          aria-valuemax={100}
          className="h-2.5 w-full overflow-hidden rounded-full bg-slate-100"
        >
          <div
            className="h-full rounded-full bg-teal-600 transition-all duration-500"
            style={{ width: `${progress.progress_percent}%` }}
          />
        </div>
        {progress.estimated_remaining_seconds !== null && (
          <p className="mt-2 text-xs text-slate-400">
            예상 소요 시간: 약 {progress.estimated_remaining_seconds}초 남음
          </p>
        )}
      </Card>
    </div>
  );
}

export default function AnalyzePage() {
  return (
    <AppShell breadcrumbs={[{ label: "Loading", href: "/analyze" }, { label: "검증 진행" }]}>
      <Suspense fallback={<LoadingState label="불러오는 중입니다..." />}>
        <AnalyzeContent />
      </Suspense>
    </AppShell>
  );
}
