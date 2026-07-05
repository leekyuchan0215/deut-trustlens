import { clsx } from "clsx";

export function Card({
  className,
  children,
  as: Component = "div",
}: {
  className?: string;
  children: React.ReactNode;
  as?: "div" | "section";
}) {
  return (
    <Component
      className={clsx(
        "rounded-2xl border border-slate-200/60 bg-white/90 shadow-[0_1px_2px_rgba(15,23,42,0.04),0_8px_24px_-12px_rgba(15,23,42,0.08)]",
        className,
      )}
    >
      {children}
    </Component>
  );
}
