import type { ReactNode } from "react";

interface StatusBadgeProps {
  statut: string;
  labels?: Record<string, string>;
  colors?: Record<string, string>;
}

export function StatusBadge({ statut, labels, colors }: StatusBadgeProps) {
  const label = (labels ?? {})[statut] ?? statut;
  const color = (colors ?? {})[statut] ?? "text-muted";
  return (
    <span
      className={`inline-flex items-center rounded-full border border-border px-2.5 py-0.5 text-xs font-semibold ${color}`}
    >
      {label}
    </span>
  );
}

export function Pill({ children }: { children: ReactNode }) {
  return (
    <span className="inline-flex items-center rounded-full border border-border bg-surface px-2.5 py-0.5 text-xs text-muted">
      {children}
    </span>
  );
}