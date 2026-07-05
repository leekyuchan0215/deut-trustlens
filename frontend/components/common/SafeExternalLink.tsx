import { ExternalLink } from "lucide-react";
import { clsx } from "clsx";

export function SafeExternalLink({
  href,
  children,
  className,
  showIcon = true,
}: {
  href: string;
  children: React.ReactNode;
  className?: string;
  showIcon?: boolean;
}) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className={clsx("inline-flex items-center gap-1 text-teal-700 hover:underline", className)}
    >
      {children}
      {showIcon && <ExternalLink className="h-3.5 w-3.5" aria-hidden="true" />}
    </a>
  );
}
