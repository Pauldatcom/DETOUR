/**
 * Six verification states for prices and places (#120). Until the backend
 * stamps them (#116), they are derived here from the server reading.
 */
import type { AppelOutilConseiller, EtatVerification, PrestationRecherche } from "../types";

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

/** True when a tool call of the turn failed on the server side. */
export function verificationEchouee(toolCalls: AppelOutilConseiller[] | undefined): boolean {
  return (toolCalls ?? []).some((call) => !STATUTS_SANS_ERREUR.has(call.statut));
}
