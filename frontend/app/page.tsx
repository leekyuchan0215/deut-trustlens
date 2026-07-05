"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Card } from "@/components/common/Card";
import { PurposeSelector } from "@/components/home/PurposeSelector";
import { RecentQuestions } from "@/components/home/RecentQuestions";
import { PromptRefinementModal } from "@/components/home/PromptRefinementModal";
import { api, ApiError } from "@/lib/api";
import { DEFAULT_ANSWER_PURPOSE, EXAMPLE_QUESTIONS, MAX_QUESTION_LENGTH } from "@/lib/constants";
import type { AnswerPurpose } from "@/lib/types";

interface RefineState {
  original: string;
  refined: string;
}

export default function HomePage() {
  const router = useRouter();
  const [question, setQuestion] = useState("");
  const [purpose, setPurpose] = useState<AnswerPurpose>(DEFAULT_ANSWER_PURPOSE);
  const [validationError, setValidationError] = useState<string | null>(null);

  const [refining, setRefining] = useState(false);
  const [refineState, setRefineState] = useState<RefineState | null>(null);

  const [analyzing, setAnalyzing] = useState(false);
  const [analyzeError, setAnalyzeError] = useState<string | null>(null);

  async function handleStartVerification() {
    const trimmed = question.trim();
    if (trimmed.length < 2) {
      setValidationError("질문은 2자 이상 입력해주세요.");
      return;
    }
    if (trimmed.length > MAX_QUESTION_LENGTH) {
      setValidationError(`질문은 최대 ${MAX_QUESTION_LENGTH}자까지 입력할 수 있습니다.`);
      return;
    }
    setValidationError(null);
    setRefining(true);
    try {
      const res = await api.refinePrompt({ question: trimmed, answer_purpose: purpose });
      setRefineState({ original: trimmed, refined: res.refined_question });
    } catch (err) {
      setValidationError(
        err instanceof ApiError ? err.message : "질문 개선 요청에 실패했습니다. 다시 시도해주세요.",
      );
    } finally {
      setRefining(false);
    }
  }

  async function handleConfirmAnalyze(finalQuestion: string) {
    if (!refineState) return;
    setAnalyzing(true);
    setAnalyzeError(null);
    try {
      const res = await api.analyze({
        question: finalQuestion,
        original_question: refineState.original,
        refined_question: refineState.refined,
        answer_purpose: purpose,
      });
      router.push(`/analyze?question_id=${res.question_id}`);
    } catch (err) {
      setAnalyzeError(
        err instanceof ApiError ? err.message : "분석 요청에 실패했습니다. 다시 시도해주세요.",
      );
      setAnalyzing(false);
    }
  }

  return (
    <AppShell>
      <div className="mx-auto flex max-w-4xl flex-col gap-6">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-slate-900 sm:text-3xl">
            AI 답변을 검증하고 더 신뢰할 수 있는 정보를 얻으세요
          </h1>
          <p className="mt-2 text-sm text-slate-500 sm:text-base">
            궁금한 내용을 질문하면 AI가 답변을 검증해드립니다.
          </p>
        </div>

        <Card className="p-5 sm:p-7">
          <label htmlFor="question-input" className="mb-3 block text-base font-bold text-slate-900">
            검증하고 싶은 질문을 입력하세요
          </label>
          <div className="relative">
            <textarea
              id="question-input"
              value={question}
              onChange={(e) => {
                setQuestion(e.target.value.slice(0, MAX_QUESTION_LENGTH));
                if (validationError) setValidationError(null);
              }}
              placeholder="예: RAG와 Fine-tuning 중 무엇이 더 좋은 방법인가요?"
              rows={5}
              maxLength={MAX_QUESTION_LENGTH}
              aria-describedby="question-help question-count"
              className="w-full resize-none rounded-xl border border-slate-200 p-4 pb-7 text-sm text-slate-800 outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500"
            />
            <span
              id="question-count"
              className="pointer-events-none absolute bottom-3 right-4 text-xs text-slate-400"
            >
              {question.length} / {MAX_QUESTION_LENGTH}
            </span>
          </div>
          <p id="question-help" className="mt-2 text-xs text-slate-400">
            구체적이고 명확한 질문일수록 더 정확한 검증이 가능합니다.
          </p>
          {validationError && (
            <p role="alert" className="mt-2 text-xs font-medium text-red-600">
              {validationError}
            </p>
          )}

          <div className="mt-5">
            <p className="mb-2 text-sm font-semibold text-slate-700">예시 질문</p>
            <div className="flex flex-wrap gap-2">
              {EXAMPLE_QUESTIONS.map((example) => (
                <button
                  key={example}
                  type="button"
                  onClick={() => setQuestion(example)}
                  className="rounded-lg border border-slate-200 bg-slate-50 px-3.5 py-2 text-xs font-medium text-slate-600 transition-colors hover:border-teal-300 hover:bg-teal-50 hover:text-teal-700"
                >
                  {example}
                </button>
              ))}
            </div>
          </div>
        </Card>

        <Card className="p-5 sm:p-7">
          <p className="mb-3 text-base font-bold text-slate-900">
            답변 목적 선택 <span className="text-sm font-normal text-slate-400">(원하는 답변의 목적을 선택하세요)</span>
          </p>
          <PurposeSelector value={purpose} onChange={setPurpose} />
        </Card>

        <button
          type="button"
          onClick={handleStartVerification}
          disabled={refining}
          className="flex items-center justify-center gap-2 rounded-xl bg-teal-700 py-3.5 text-base font-semibold text-white shadow-sm transition-colors hover:bg-teal-800 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {refining ? "질문을 분석하는 중..." : "검증 시작하기 →"}
        </button>

        <RecentQuestions />
      </div>

      {refineState && (
        <PromptRefinementModal
          originalQuestion={refineState.original}
          refinedQuestion={refineState.refined}
          submitting={analyzing}
          error={analyzeError}
          onClose={() => {
            setRefineState(null);
            setAnalyzeError(null);
          }}
          onConfirm={handleConfirmAnalyze}
        />
      )}
    </AppShell>
  );
}
