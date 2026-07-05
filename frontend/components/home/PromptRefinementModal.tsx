"use client";

import { useEffect, useRef, useState } from "react";
import { Pencil, X } from "lucide-react";
import { MAX_QUESTION_LENGTH } from "@/lib/constants";

export function PromptRefinementModal({
  originalQuestion,
  refinedQuestion,
  submitting,
  error,
  onClose,
  onConfirm,
}: {
  originalQuestion: string;
  refinedQuestion: string;
  submitting: boolean;
  error: string | null;
  onClose: () => void;
  onConfirm: (question: string) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(refinedQuestion);
  const dialogRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    document.body.style.overflow = "hidden";
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = "";
      document.removeEventListener("keydown", onKey);
    };
  }, [onClose]);

  useEffect(() => {
    dialogRef.current?.focus();
  }, []);

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-sm">
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="refine-modal-title"
        tabIndex={-1}
        className="w-full max-w-2xl rounded-2xl bg-white p-6 shadow-2xl outline-none sm:p-8"
        onKeyDown={(e) => e.stopPropagation()}
      >
        <div className="mb-1 flex items-start justify-between">
          <h2 id="refine-modal-title" className="text-xl font-bold text-slate-900">
            질문 개선하기
          </h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="닫기"
            className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
          >
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>
        <p className="mb-6 text-sm text-slate-500">AI가 질문을 더 명확하고 구체적으로 개선했습니다.</p>

        <div className="mb-4">
          <label htmlFor="original-question" className="mb-1.5 block text-sm font-semibold text-slate-700">
            원본 질문
          </label>
          <div className="relative">
            <textarea
              id="original-question"
              readOnly
              value={originalQuestion}
              rows={2}
              className="w-full resize-none rounded-xl border border-slate-200 bg-slate-50 p-3 pb-6 text-sm text-slate-600"
            />
            <span className="pointer-events-none absolute bottom-2 right-3 text-xs text-slate-400">
              {originalQuestion.length} / {MAX_QUESTION_LENGTH}
            </span>
          </div>
        </div>

        <div className="mb-6">
          <label htmlFor="refined-question" className="mb-1.5 block text-sm font-semibold text-slate-700">
            개선된 질문 (AI 제안)
          </label>
          <div className="relative">
            <textarea
              id="refined-question"
              readOnly={!editing}
              value={draft}
              maxLength={MAX_QUESTION_LENGTH}
              onChange={(e) => setDraft(e.target.value)}
              rows={3}
              className={`w-full resize-none rounded-xl border p-3 pb-6 text-sm ${
                editing
                  ? "border-teal-400 bg-white text-slate-800"
                  : "border-teal-200 bg-teal-50/60 text-slate-800"
              }`}
            />
            <span className="pointer-events-none absolute bottom-2 right-3 text-xs text-slate-400">
              {draft.length} / {MAX_QUESTION_LENGTH}
            </span>
          </div>
        </div>

        {error && (
          <p role="alert" className="mb-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </p>
        )}

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          {editing ? (
            <button
              type="button"
              disabled={submitting || draft.trim().length < 2}
              onClick={() => onConfirm(draft.trim())}
              className="flex-1 rounded-xl bg-teal-700 py-3 text-sm font-semibold text-white transition-colors hover:bg-teal-800 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {submitting ? "요청 중..." : "수정한 질문 사용"}
            </button>
          ) : (
            <button
              type="button"
              disabled={submitting}
              onClick={() => onConfirm(refinedQuestion)}
              className="flex-1 rounded-xl bg-teal-700 py-3 text-sm font-semibold text-white transition-colors hover:bg-teal-800 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {submitting ? "요청 중..." : "개선된 질문 사용"}
            </button>
          )}
          <button
            type="button"
            disabled={submitting}
            onClick={() => setEditing(true)}
            className="flex items-center justify-center gap-1.5 px-4 py-3 text-sm font-medium text-slate-600 hover:text-slate-900 disabled:opacity-50"
          >
            <Pencil className="h-4 w-4" aria-hidden="true" />
            직접 수정
          </button>
          <button
            type="button"
            disabled={submitting}
            onClick={() => onConfirm(originalQuestion)}
            className="px-4 py-3 text-sm font-medium text-slate-500 hover:text-slate-800 disabled:opacity-50"
          >
            원본 질문 사용
          </button>
        </div>
      </div>
    </div>
  );
}
