import { ETAT_LABELS } from "../../lib/verification";
import type { EtatVerification } from "../../types";

/*
 * One style per state, 2026 palette only. Brick marks what changed or failed;
 * yellow is never used as text on a light background.
 */
const STYLES: Record<EtatVerification, string> = {
  verified: "border-ink/20 bg-sky/40 text-ink",
  checking: "border-dashed border-ballast/60 bg-card text-ballast",
  modified: "border-brick bg-brick/10 text-brick",
  unavailable: "border-brick/50 bg-card text-brick",
  not_verified: "border-line bg-card text-ballast",
  error: "border-brick bg-card text-brick",
};

interface VerificationStateBadgeProps {
  state: EtatVerification;
  /** Optional detail after the label, e.g. the check time. */
  detail?: string;
}

/** Verification state in words, never a color alone. */
export function VerificationStateBadge({ state, detail }: VerificationStateBadgeProps) {
  return (
    <span
      data-state={state}
      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium whitespace-nowrap ${STYLES[state]}`}
    >
      {ETAT_LABELS[state]}
      {detail ? ` · ${detail}` : ""}
    </span>
  );
}
