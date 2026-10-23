import { formatAmount, formatClock, seatsSentence } from "../../lib/tone";
import type { EtatVerification, PrestationRecherche } from "../../types";
import { VerificationStateBadge } from "./VerificationStateBadge";

const TYPE_LABELS: Record<string, string> = {
  transport: "Transport",
  hebergement: "Hébergement",
  activite: "Activité",
};

interface OptionCardProps {
  result: PrestationRecherche;
  state: EtatVerification;
  checkedAt: string | null;
  /** Previous price per person, when the state is "modified". */
  previousPrice?: number;
}

function checkTime(iso: string | null): string {
  if (!iso) return "";
  const moment = new Date(iso);
  return isNaN(moment.getTime()) ? "" : formatClock(moment);
}

/** One option returned by the assistant: price per person, seats, verification state. */
export function OptionCard({ result, state, checkedAt, previousPrice }: OptionCardProps) {
  const time = state === "verified" || state === "modified" ? checkTime(checkedAt) : "";
  return (
    <article className="rounded-xl border border-line bg-white p-3 text-sm text-ink">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <h4 className="font-display font-semibold tracking-tight">{result.nom}</h4>
          <p className="text-xs text-ballast">{TYPE_LABELS[result.type] ?? result.type}</p>
        </div>
        <VerificationStateBadge state={state} detail={time} />
      </div>
      {state === "unavailable" ? (
        <p className="mt-2 text-brick">Complet à cette date.</p>
      ) : state === "not_verified" ? (
        <p className="mt-2 text-ballast">Prix et places à vérifier.</p>
      ) : (
        <div className="mt-2 space-y-0.5">
          <p className={state === "modified" ? "font-semibold text-brick" : "font-semibold"}>
            {state === "modified" && previousPrice !== undefined && (
              <span className="font-normal text-ballast line-through">
                {formatAmount(previousPrice)}
              </span>
            )}{" "}
            {formatAmount(result.prix_unitaire_eur)} par personne
          </p>
          <p className="text-xs text-ballast">
            {formatAmount(result.prix_total_eur)} pour le groupe
            {result.places_restantes !== undefined
              ? ` · ${seatsSentence(result.places_restantes)}`
              : ""}
          </p>
        </div>
      )}
    </article>
  );
}
