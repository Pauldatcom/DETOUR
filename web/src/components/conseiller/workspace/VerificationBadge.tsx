import { formatCheckedAt } from "./labels";

export type VerificationState = "verified" | "copied" | "changed" | "unverified";

interface VerificationBadgeProps {
  state: VerificationState;
  checkedAt?: string | null;
}

const STYLES: Record<VerificationState, string> = {
  verified: "border-ink/20 bg-sky/40 text-ink",
  copied: "border-brick/40 bg-card text-brick",
  changed: "border-brick bg-brick/10 text-brick",
  unverified: "border-line bg-card text-ballast",
};

/** Says, in words, whether a price was checked against the server and when. */
export function VerificationBadge({ state, checkedAt }: VerificationBadgeProps) {
  const at = formatCheckedAt(checkedAt);
  const text = {
    verified: at ? `Vérifié le ${at}` : "Vérifié",
    copied: "Repris de la v1 · non relu",
    changed: "Prix ou disponibilité modifiés",
    unverified: "Non vérifié",
  }[state];
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium whitespace-nowrap ${STYLES[state]}`}
    >
      {text}
    </span>
  );
}
