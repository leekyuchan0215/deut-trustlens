"use client";

import { clsx } from "clsx";
import { ANSWER_PURPOSE_OPTIONS } from "@/lib/constants";
import type { AnswerPurpose } from "@/lib/types";

export function PurposeSelector({
  value,
  onChange,
}: {
  value: AnswerPurpose;
  onChange: (value: AnswerPurpose) => void;
}) {
  return (
    <div
      role="radiogroup"
      aria-label="답변 목적 선택"
      className="flex flex-wrap gap-2"
    >
      {ANSWER_PURPOSE_OPTIONS.map((option) => {
        const active = option.value === value;
        return (
          <button
            key={option.value}
            type="button"
            role="radio"
            aria-checked={active}
            onClick={() => onChange(option.value)}
            className={clsx(
              "flex items-center gap-2 rounded-xl border px-4 py-2.5 text-sm font-medium transition-colors",
              active
                ? "border-teal-600 bg-teal-50 text-teal-700"
                : "border-slate-200 bg-white text-slate-600 hover:border-slate-300",
            )}
          >
            <span
              className={clsx(
                "h-2 w-2 rounded-full",
                active ? "bg-teal-600" : "bg-slate-300",
              )}
              aria-hidden="true"
            />
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
