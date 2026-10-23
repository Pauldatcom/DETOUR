/**
 * Verification helpers for prices and places. The advisor view uses six
 * states (#120); the traveler view uses the five states from #127.
 */
import type {
  AppelOutilConseiller,
  ChangementLecture,
  EtatVerification,
  Prestation,
  PrestationRecherche,
} from "../types";

/** Five traveler-facing states (#127). The advisor model also has "error". */
export type EtatTarifVoyageur =
  "verified" | "checking" | "modified" | "unavailable" | "not_verified";

export const ETAT_LABELS: Record<EtatVerification, string> = {
  verified: "Vérifié",
  checking: "Vérification en cours",
  modified: "Prix modifié",
  unavailable: "Indisponible",
  not_verified: "Non vérifié",
  error: "Vérification impossible",
};

/** Tool statuses that mean the assistant called a tool without a server error. */
const STATUTS_SANS_ERREUR = new Set(["ok", "refuse"]);

/**
 * State of one result. `previous` is the same service in an earlier reading
 * of this conversation, used to flag a price change.
 */
export function etatPrestation(
  result: PrestationRecherche,
  checkedAt: string | null | undefined,
  previous?: PrestationRecherche,
): EtatVerification {
  if (typeof result.prix_unitaire_eur !== "number" || !checkedAt) return "not_verified";
  if (result.disponible === false) return "unavailable";
  if (previous && previous.prix_unitaire_eur !== result.prix_unitaire_eur) return "modified";
  return "verified";
}

/** A timestamp we can actually show next to a price. */
export function dateVerificationValide(value: string | null | undefined): value is string {
  if (!value) return false;
  return !isNaN(new Date(value).getTime());
}

/**
 * Traveler-facing state of one proposal line. A price is never confirmed
 * without a positive amount and a dated server reading. A newer reading that
 * changed the price becomes "modified" only when it too carries a date.
 */
export function etatTarifVoyageur(
  service: Prestation,
  change?: ChangementLecture | null,
): EtatTarifVoyageur {
  const priceConfirmed =
    service.verification === "verifie" &&
    typeof service.prix_unitaire_eur === "number" &&
    service.prix_unitaire_eur >= 0 &&
    dateVerificationValide(service.consulte_le);

  if (!priceConfirmed) return "not_verified";

  // A v2 line copied from v1 has an old date: never present it as current.
  if (service.copie_depuis_v1) return "checking";

  if (change && !change.inchange) {
    if (change.prix_change) {
      return dateVerificationValide(change.consulte_le) ? "modified" : "checking";
    }
    if (!dateVerificationValide(change.consulte_le)) return "checking";
  }

  // The latest reading wins over the old line, especially when a place that
  // was unavailable has become bookable again.
  const availability =
    change && !change.inchange && dateVerificationValide(change.consulte_le)
      ? change.disponible_apres
      : service.disponible;
  if (availability === false) return "unavailable";
  if (availability === null) return "not_verified";
  return "verified";
}

/** True when a tool call of the turn failed on the server side. */
export function verificationEchouee(toolCalls: AppelOutilConseiller[] | undefined): boolean {
  return (toolCalls ?? []).some((call) => !STATUTS_SANS_ERREUR.has(call.statut));
}
