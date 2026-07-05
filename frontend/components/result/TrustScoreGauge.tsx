import { formatScore } from "@/lib/formatters";

export function TrustScoreGauge({ score, grade }: { score: number; grade: string }) {
  const radius = 64;
  const circumference = 2 * Math.PI * radius;
  const clamped = Math.max(0, Math.min(100, score));
  const dash = (clamped / 100) * circumference;

  return (
    <div className="flex flex-col items-center">
      <svg width="160" height="160" viewBox="0 0 160 160" role="img" aria-label={`종합 신뢰도 점수 ${formatScore(score)}점, ${grade}`}>
        <defs>
          <linearGradient id="trust-score-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#6366f1" />
            <stop offset="100%" stopColor="#0d9488" />
          </linearGradient>
        </defs>
        <circle cx="80" cy="80" r={radius} fill="none" stroke="#e2e8f0" strokeWidth="14" />
        <circle
          cx="80"
          cy="80"
          r={radius}
          fill="none"
          stroke="url(#trust-score-gradient)"
          strokeWidth="14"
          strokeLinecap="round"
          strokeDasharray={`${dash} ${circumference - dash}`}
          strokeDashoffset={circumference / 4}
          transform="scale(1, -1)"
          style={{ transformOrigin: "80px 80px" }}
        />
        <text x="80" y="76" textAnchor="middle" className="fill-slate-900 text-3xl font-bold">
          {formatScore(score)}
        </text>
        <text x="80" y="98" textAnchor="middle" className="fill-slate-400 text-xs">
          /100
        </text>
      </svg>
      <p className="mt-1 text-sm font-semibold text-teal-700">{grade}</p>
    </div>
  );
}
