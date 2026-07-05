import { CheckCircle2, Circle, Diamond, Grid3x3, Loader2, Triangle, XCircle } from "lucide-react";
import { Card } from "@/components/common/Card";
import { PROVIDER_LABEL } from "@/lib/constants";
import type { ModelStatus } from "@/lib/types";

const PROVIDER_ICON = {
  gpt: Grid3x3,
  claude: Triangle,
  gemini: Diamond,
} as const;

const STATUS_META = {
  pending: { label: "대기", className: "text-slate-400", Icon: Circle },
  processing: { label: "진행 중", className: "text-teal-600", Icon: Loader2 },
  success: { label: "완료", className: "text-emerald-600", Icon: CheckCircle2 },
  failed: { label: "실패", className: "text-red-600", Icon: XCircle },
} as const;

export function ModelStatusCard({ status }: { status: ModelStatus }) {
  const ProviderIcon = PROVIDER_ICON[status.provider];
  const meta = STATUS_META[status.status];
  const StatusIcon = meta.Icon;

  return (
    <Card className="flex items-center justify-between gap-3 px-4 py-3.5">
      <div className="flex items-center gap-3">
        <span className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-100 text-slate-600">
          <ProviderIcon className="h-4 w-4" aria-hidden="true" />
        </span>
        <div>
          <p className="text-sm font-semibold text-slate-900">{status.model_name}</p>
          <p className="text-xs text-slate-400">{PROVIDER_LABEL[status.provider]}</p>
        </div>
      </div>
      <div className={`flex items-center gap-1.5 text-sm font-medium ${meta.className}`}>
        <StatusIcon
          className={`h-4 w-4 ${status.status === "processing" ? "animate-spin" : ""}`}
          aria-hidden="true"
        />
        {meta.label}
        {status.latency_ms !== null && (
          <span className="text-xs text-slate-400">{(status.latency_ms / 1000).toFixed(1)}초</span>
        )}
      </div>
    </Card>
  );
}
