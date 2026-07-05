export function formatScore(score: number): string {
  return Number.isInteger(score) ? String(score) : score.toFixed(1);
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "-";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "-";
  const yyyy = date.getFullYear();
  const mm = String(date.getMonth() + 1).padStart(2, "0");
  const dd = String(date.getDate()).padStart(2, "0");
  return `${yyyy}.${mm}.${dd}`;
}

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return "-";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "-";
  const yyyy = date.getFullYear();
  const mm = String(date.getMonth() + 1).padStart(2, "0");
  const dd = String(date.getDate()).padStart(2, "0");
  const hh = String(date.getHours()).padStart(2, "0");
  const min = String(date.getMinutes()).padStart(2, "0");
  return `${yyyy}.${mm}.${dd} ${hh}:${min}`;
}

// score band follows docs/TRUST_SCORE.md grade thresholds; used only for badge color, not recomputation.
export type ScoreBand = "very-high" | "high" | "medium" | "low" | "very-low";

export function scoreBand(score: number): ScoreBand {
  if (score >= 90) return "very-high";
  if (score >= 75) return "high";
  if (score >= 60) return "medium";
  if (score >= 40) return "low";
  return "very-low";
}

export function scoreBadgeClasses(score: number): string {
  const band = scoreBand(score);
  switch (band) {
    case "very-high":
    case "high":
      return "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200";
    case "medium":
      return "bg-amber-50 text-amber-700 ring-1 ring-amber-200";
    default:
      return "bg-red-50 text-red-700 ring-1 ring-red-200";
  }
}

export function relevancePercent(hybridScore: number): number {
  return Math.round(hybridScore * 100);
}

export function riskLevelClasses(level: "low" | "medium" | "high"): string {
  switch (level) {
    case "low":
      return "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200";
    case "medium":
      return "bg-amber-50 text-amber-700 ring-1 ring-amber-200";
    case "high":
      return "bg-red-50 text-red-700 ring-1 ring-red-200";
  }
}

export function verificationStatusClasses(
  status: "pending" | "verified" | "weak_evidence" | "unsupported" | "contradicted",
): string {
  switch (status) {
    case "verified":
      return "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200";
    case "weak_evidence":
      return "bg-amber-50 text-amber-700 ring-1 ring-amber-200";
    case "unsupported":
      return "bg-slate-100 text-slate-600 ring-1 ring-slate-200";
    case "contradicted":
      return "bg-red-50 text-red-700 ring-1 ring-red-200";
    default:
      return "bg-slate-100 text-slate-600 ring-1 ring-slate-200";
  }
}

export function consensusLevelLabel(level: "high" | "medium" | "low"): string {
  switch (level) {
    case "high":
      return "높음";
    case "medium":
      return "보통";
    case "low":
      return "낮음";
  }
}

export function riskLevelLabel(level: "low" | "medium" | "high"): string {
  switch (level) {
    case "low":
      return "낮음";
    case "medium":
      return "보통";
    case "high":
      return "높음";
  }
}
