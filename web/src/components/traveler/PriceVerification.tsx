import type { ChangementLecture, Prestation, Proposition } from "../../types";
import {
  dateVerificationValide,
  etatTarifVoyageur,
  type EtatTarifVoyageur,
} from "../../lib/verification";
import {
  formatAmount,
  perPersonSentence,
  priceCheckedSentence,
  seatsSentence,
  whenChecked,
} from "../../lib/tone";

interface PriceVerificationProps {
  service: Prestation;
  change?: ChangementLecture | null;
  seats?: number | null;
  /** Smaller text for the proposal list card. */
  compact?: boolean;
  /** Show the server source on verified lines (list card). */
  showSource?: boolean;
}

function availabilityText(available: boolean | null, seats: number | null): string {
  if (available === false) return "Complet à cette date.";
  if (available === null) return "Disponibilité non vérifiée.";
  return seatsSentence(seats) || "Disponible à cette date.";
}

function availabilityTone(available: boolean | null, seats: number | null): string {
  if (available === false || (seats !== null && seats <= 0)) return "font-medium text-brick";
  return "text-ballast";
}

/**
 * One readable verification state for a traveler price and availability (#127).
 *
 * The five states are rendered here and nowhere else, so a card and a detail
 * page cannot drift apart. An amount is only shown when it carries a date.
 */
export function PriceVerification({
  service,
  change,
  seats = null,
  compact = false,
  showSource = false,
}: PriceVerificationProps) {
  const state: EtatTarifVoyageur = etatTarifVoyageur(service, change);
  const textSize = compact ? "text-xs" : "text-sm";
  const currentChange = change && !change.inchange ? change : null;
  const changeCheckedAt =
    currentChange && dateVerificationValide(currentChange.consulte_le)
      ? currentChange.consulte_le
      : null;
  const availability =
    currentChange && changeCheckedAt ? currentChange.disponible_apres : service.disponible;
  const availabilityCheckedAt = changeCheckedAt ?? service.consulte_le;
  const availabilityHasOwnDate =
    state !== "modified" &&
    dateVerificationValide(availabilityCheckedAt) &&
    availabilityCheckedAt !== service.consulte_le;

  if (state === "not_verified") {
    return (
      <div className={`mt-1 space-y-0.5 ${textSize}`}>
        <p className="font-medium text-ink">Prix non vérifié.</p>
        <p className="text-ballast">Disponibilité non vérifiée.</p>
        {service.copie_depuis_v1 && (
          <p className="text-ballast">Prix repris de la proposition précédente, non relu.</p>
        )}
      </div>
    );
  }

  if (state === "checking") {
    return (
      <div className={`mt-1 space-y-0.5 ${textSize}`}>
        <p className="font-medium text-ink">Vérification en cours…</p>
        <p className="text-ballast">Prix et disponibilité en cours de vérification.</p>
        {service.copie_depuis_v1 && (
          <p className="text-ballast">Prix repris de la proposition précédente, non relu.</p>
        )}
      </div>
    );
  }

  if (state === "unavailable") {
    return (
      <div className={`mt-1 space-y-0.5 ${textSize}`}>
        <p className="font-medium text-brick">Complet à cette date.</p>
        {dateVerificationValide(availabilityCheckedAt) && (
          <p className="text-ballast">
            Disponibilité vérifiée {whenChecked(availabilityCheckedAt)}.
          </p>
        )}
      </div>
    );
  }

  const verifiedPrice =
    state === "modified" ? currentChange?.prix_apres : service.prix_unitaire_eur;
  if (typeof verifiedPrice !== "number") {
    return (
      <div className={`mt-1 space-y-0.5 ${textSize}`}>
        <p className="font-medium text-ink">Prix non vérifié.</p>
        <p className="text-ballast">Disponibilité non vérifiée.</p>
      </div>
    );
  }

  const priceCheckedAt = state === "modified" ? changeCheckedAt : service.consulte_le;
  const groupTotal =
    state === "modified" ? verifiedPrice * service.quantite : service.prix_total_eur;
  const priceTone = state === "modified" ? "font-semibold text-brick" : "font-semibold text-ink";

  return (
    <div className={`mt-1 space-y-0.5 ${textSize}`}>
      <p className={priceTone}>{perPersonSentence(verifiedPrice)}</p>
      <p className="text-ballast">{priceCheckedSentence(priceCheckedAt)}</p>

      {state === "modified" && currentChange && (
        <p className="rounded-lg border border-brick/40 bg-brick/10 px-3 py-2 text-brick">
          Prix modifié. Avant : {formatAmount(currentChange.prix_avant)} par personne
          {dateVerificationValide(service.consulte_le)
            ? `, vérifié ${whenChecked(service.consulte_le)}`
            : ""}
          .
        </p>
      )}

      <p className={availabilityTone(availability, seats)}>
        {availabilityText(availability, seats)}
      </p>
      {availabilityHasOwnDate && dateVerificationValide(availabilityCheckedAt) && (
        <p className="text-ballast">Disponibilité vérifiée {whenChecked(availabilityCheckedAt)}.</p>
      )}

      {service.quantite > 1 && groupTotal !== null && (
        <p className="text-ballast">
          {formatAmount(groupTotal)} au total pour ce poste
          {dateVerificationValide(priceCheckedAt)
            ? `, au prix vérifié ${whenChecked(priceCheckedAt)}`
            : ""}
          .
        </p>
      )}

      {showSource && service.source && (
        <p className="text-[11px] text-ballast/60">{service.source}</p>
      )}
    </div>
  );
}

interface ProposalTotalProps {
  proposition: Proposition;
  travelers?: number | null;
  /** Larger total block on the proposal detail page. */
  large?: boolean;
}

/**
 * Proposal total, dated from the latest verified line. When nothing is
 * verified there is no amount at all, and unverified lines are named in a
 * sentence rather than a price footnote.
 */
export function ProposalTotal({ proposition, travelers, large = false }: ProposalTotalProps) {
  const verified = proposition.prestations.filter(
    (line) => line.verification === "verifie" && dateVerificationValide(line.consulte_le),
  );
  const latest = verified.reduce<string | null>((current, line) => {
    if (!current) return line.consulte_le;
    return new Date(line.consulte_le as string) > new Date(current) ? line.consulte_le : current;
  }, null);
  const unverified = proposition.prestations.filter(
    (line) => line.verification !== "verifie",
  ).length;
  const copied = proposition.prestations.filter((line) => line.copie_depuis_v1).length;
  const priceChanges = (proposition.changements ?? []).filter(
    (change) => !change.inchange && change.prix_change,
  ).length;

  const amountClass = large ? "font-display text-2xl font-extrabold" : "font-extrabold text-ink";
  const detailClass = large ? "text-sm text-ballast" : "text-[10px] leading-tight text-ballast/60";
  const travelerLabel =
    travelers && travelers > 0
      ? ` pour ${travelers} voyageur${travelers > 1 ? "s" : ""}`
      : " au total";

  if (!latest) {
    return (
      <div>
        <p className={amountClass}>Prix non vérifié.</p>
        <p className={`mt-0.5 ${detailClass}`}>
          Aucune prestation vérifiée ne permet d’afficher un total.
        </p>
      </div>
    );
  }

  return (
    <div>
      <p className={`${amountClass} meta-nowrap`}>
        {formatAmount(proposition.prix_total_eur)}
        {travelerLabel}.
      </p>
      <p className={`mt-0.5 ${detailClass}`}>
        {unverified > 0 ? "Total des prestations vérifiées" : "Prix total vérifié"}{" "}
        {whenChecked(latest)}.
      </p>
      {unverified > 0 && (
        <p className={`mt-0.5 ${detailClass}`}>
          Hors {unverified} prestation{unverified > 1 ? "s" : ""} non vérifiée
          {unverified > 1 ? "s" : ""}.
        </p>
      )}
      {copied > 0 && (
        <p className={`mt-0.5 ${detailClass}`}>
          Dont {copied} prix repris de la proposition précédente.
        </p>
      )}
      {priceChanges > 0 && (
        <p className={`mt-0.5 ${detailClass}`}>Hors changements de prix signalés.</p>
      )}
    </div>
  );
}
