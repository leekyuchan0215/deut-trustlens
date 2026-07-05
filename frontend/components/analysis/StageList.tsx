import { Check, Loader2 } from "lucide-react";
import type { DisplayStep } from "@/lib/types";

export function StageList({ steps }: { steps: DisplayStep[] }) {
  return (
    <ol className="flex flex-col gap-1">
      {steps.map((step, idx) => {
        const isCompleted = step.status === "completed";
        const isProcessing = step.status === "processing";
        return (
          <li key={step.stage} className="flex items-center gap-4 rounded-xl px-3 py-3">
            <span
              className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-semibold ${
                isCompleted
                  ? "bg-emerald-100 text-emerald-600"
                  : isProcessing
                    ? "bg-teal-100 text-teal-600"
                    : "bg-slate-100 text-slate-400"
              }`}
              aria-hidden="true"
            >
              {isCompleted ? (
                <Check className="h-4 w-4" />
              ) : isProcessing ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                idx + 1
              )}
            </span>
            <span
              className={`flex-1 text-sm ${
                isProcessing ? "font-semibold text-slate-900" : "text-slate-700"
              }`}
            >
              {step.label}
            </span>
            {isCompleted && step.duration_ms !== null && (
              <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700">
                {(step.duration_ms / 1000).toFixed(1)}초
              </span>
            )}
            {isProcessing && (
              <span className="rounded-full bg-teal-50 px-2.5 py-1 text-xs font-medium text-teal-700">
                진행 중
              </span>
            )}
          </li>
        );
      })}
    </ol>
  );
}
