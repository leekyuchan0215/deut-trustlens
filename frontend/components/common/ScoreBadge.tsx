import { clsx } from "clsx";
import { formatScore, scoreBadgeClasses } from "@/lib/formatters";

export function ScoreBadge({ score, className }: { score: number; className?: string }) {
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-full px-2.5 py-1 text-sm font-semibold",
        scoreBadgeClasses(score),
        className,
      )}
    >
      {formatScore(score)}점
    </span>
  );
}
