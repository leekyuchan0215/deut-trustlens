export function LogoMark({ size = 36 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 40 40"
      fill="none"
      aria-hidden="true"
      className="shrink-0"
    >
      <circle cx="16" cy="20" r="12" stroke="#f59e0b" strokeWidth="4" />
      <circle cx="24" cy="20" r="12" stroke="#0d9488" strokeWidth="4" />
    </svg>
  );
}

export function Logo() {
  return (
    <div className="flex items-center gap-2.5">
      <LogoMark />
      <div className="leading-tight">
        <div className="text-lg font-bold text-slate-900">TrustLens</div>
        <div className="text-[10px] font-medium tracking-wide text-slate-400">
          AI ANSWER VERIFICATION
        </div>
      </div>
    </div>
  );
}
