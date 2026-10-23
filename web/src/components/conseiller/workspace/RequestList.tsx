import { STATUT_LABELS, formatDateTime } from "../../../lib/format";
import type { Demande } from "../../../types";
import { formatDay } from "./labels";

interface RequestListProps {
  requests: Demande[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

const DEADLINE_STYLES: Record<string, string> = {
  ok: "text-ballast",
  approche: "font-medium text-ink",
  depassee: "font-medium text-brick",
};

/** Requests sorted by response deadline; the selected one opens on the right. */
export function RequestList({ requests, selectedId, onSelect }: RequestListProps) {
  return (
    <ul className="space-y-2" aria-label="Demandes des voyageurs">
      {requests.map((r) => {
        const selected = r.id === selectedId;
        return (
          <li key={r.id}>
            <button
              type="button"
              onClick={() => onSelect(r.id)}
              aria-current={selected ? "true" : undefined}
              className={`w-full rounded-xl border px-4 py-3 text-left transition ${
                selected ? "border-ink bg-card" : "border-line bg-card/60 hover:border-ink/40"
              }`}
            >
              <span className="flex items-baseline justify-between gap-2">
                <span className="font-medium text-ink">{r.client?.nom ?? "Voyageur"}</span>
                <span className="text-xs text-ballast">{STATUT_LABELS[r.statut] ?? r.statut}</span>
              </span>
              <span className="mt-0.5 block text-sm text-ink">
                {r.demande.destination} · {formatDay(r.demande.date_depart)} ·{" "}
                {r.demande.nombre_voyageurs} pers.
              </span>
              {r.echeance_cible && (
                <span
                  className={`mt-1 block text-xs ${DEADLINE_STYLES[r.echeance_statut ?? "ok"] ?? "text-ballast"}`}
                >
                  {r.echeance_statut === "depassee" ? "Échéance dépassée · " : "Répondre avant le "}
                  {formatDateTime(r.echeance_cible)}
                </span>
              )}
            </button>
          </li>
        );
      })}
    </ul>
  );
}
