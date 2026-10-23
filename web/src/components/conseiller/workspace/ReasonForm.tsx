import { useId, useState, type FormEvent, type ReactNode } from "react";

interface ReasonFormProps {
  title: string;
  confirmLabel: string;
  reasonRequired: boolean;
  /** Second text field, e.g. correction instructions. Required when shown. */
  instructionsLabel?: string;
  /** Extra fields rendered above the reason (e.g. a replacement select). */
  children?: ReactNode;
  busy?: boolean;
  onSubmit: (reason: string, instructions: string) => void;
  onCancel: () => void;
}

/** Inline form that records why the advisor made a decision. */
export function ReasonForm({
  title,
  confirmLabel,
  reasonRequired,
  instructionsLabel,
  children,
  busy = false,
  onSubmit,
  onCancel,
}: ReasonFormProps) {
  const id = useId();
  const [reason, setReason] = useState("");
  const [instructions, setInstructions] = useState("");
  const [error, setError] = useState("");

  function submit(event: FormEvent) {
    event.preventDefault();
    if (reasonRequired && !reason.trim()) {
      setError("Indiquez le motif de votre décision.");
      return;
    }
    if (instructionsLabel && !instructions.trim()) {
      setError("Indiquez les instructions de correction.");
      return;
    }
    setError("");
    onSubmit(reason.trim(), instructions.trim());
  }

  return (
    <form onSubmit={submit} className="mt-3 space-y-3 rounded-xl border border-line bg-chalk p-4">
      <p className="text-sm font-medium text-ink">{title}</p>
      {children}
      <div>
        <label htmlFor={`${id}-reason`} className="block text-xs text-ballast">
          Motif {reasonRequired ? "(obligatoire)" : "(facultatif)"}
        </label>
        <textarea
          id={`${id}-reason`}
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          rows={2}
          className="mt-1 w-full rounded-lg border border-line bg-card px-3 py-2 text-sm text-ink"
        />
      </div>
      {instructionsLabel && (
        <div>
          <label htmlFor={`${id}-instructions`} className="block text-xs text-ballast">
            {instructionsLabel} (obligatoire)
          </label>
          <textarea
            id={`${id}-instructions`}
            value={instructions}
            onChange={(e) => setInstructions(e.target.value)}
            rows={2}
            className="mt-1 w-full rounded-lg border border-line bg-card px-3 py-2 text-sm text-ink"
          />
        </div>
      )}
      {error && (
        <p role="alert" className="text-xs text-brick">
          {error}
        </p>
      )}
      <div className="flex flex-wrap gap-2">
        <button
          type="submit"
          disabled={busy}
          className="rounded-full bg-ink px-4 py-2 text-sm font-semibold text-chalk transition hover:bg-ink/90"
        >
          {confirmLabel}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="rounded-full border border-line px-4 py-2 text-sm font-semibold text-ink transition hover:border-ink"
        >
          Annuler
        </button>
      </div>
    </form>
  );
}
