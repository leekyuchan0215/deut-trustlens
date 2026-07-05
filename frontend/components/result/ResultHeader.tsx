"use client";

import Link from "next/link";
import { BadgeCheck, FileDown, Share2 } from "lucide-react";
import { Card } from "@/components/common/Card";
import { useToast } from "@/components/common/Toast";
import { ANSWER_PURPOSE_LABEL, NOT_READY_MESSAGE } from "@/lib/constants";
import type { AnswerPurpose } from "@/lib/types";

export function ResultHeader({
  questionId,
  selectedQuestion,
  originalQuestion,
  refinedQuestion,
  answerPurpose,
}: {
  questionId: string;
  selectedQuestion: string;
  originalQuestion: string;
  refinedQuestion: string;
  answerPurpose: AnswerPurpose;
}) {
  const { showToast } = useToast();

  return (
    <div className="flex flex-col gap-4">
      <Link href="/history" className="flex items-center gap-1 text-sm font-medium text-teal-700 hover:underline">
        &larr; 목록으로 돌아가기
      </Link>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <h1 className="text-xl font-bold text-slate-900 sm:text-2xl">{selectedQuestion}</h1>
        <div className="flex shrink-0 gap-2">
          <button
            type="button"
            onClick={() => showToast(NOT_READY_MESSAGE)}
            className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3.5 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50"
          >
            <Share2 className="h-4 w-4" aria-hidden="true" />
            공유
          </button>
          <button
            type="button"
            onClick={() => showToast(NOT_READY_MESSAGE)}
            className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3.5 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50"
          >
            <FileDown className="h-4 w-4" aria-hidden="true" />
            리포트 저장
          </button>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <span className="inline-flex items-center gap-1.5 rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700">
          <BadgeCheck className="h-3.5 w-3.5" aria-hidden="true" />
          AI Judge 검증 완료
        </span>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
          답변 목적: {ANSWER_PURPOSE_LABEL[answerPurpose]}
        </span>
        <span className="rounded-full bg-teal-50 px-3 py-1 text-xs font-medium text-teal-700">
          Question ID: {questionId}
        </span>
      </div>

      <Card className="grid grid-cols-1 divide-y divide-slate-100 sm:grid-cols-2 sm:divide-x sm:divide-y-0">
        <div className="p-5">
          <p className="mb-1.5 text-sm font-semibold text-slate-500">원본 질문</p>
          <p className="text-sm text-slate-800">{originalQuestion}</p>
        </div>
        <div className="p-5">
          <p className="mb-1.5 text-sm font-semibold text-slate-500">개선된 질문</p>
          <p className="text-sm text-slate-800">{refinedQuestion}</p>
        </div>
      </Card>
    </div>
  );
}
