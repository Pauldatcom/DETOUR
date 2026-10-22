/** Labels and formatters shared by the advisor workspace (#111). */

export const TRIP_TYPE_LABELS: Record<string, string> = {
  "trek-randonnee": "Trek / randonnée",
  "lune-de-miel": "Lune de miel",
  "voyage-familial": "Voyage familial",
  autres: "Autre",
};

export const LEVEL_LABELS: Record<string, string> = {
  calme: "Calme",
  modere: "Modéré",
  intense: "Intense",
};

export const QUALIFICATION_LABELS: Record<string, string> = {
  incomplet: "Incomplète",
  en_cours: "En cours",
  pret_relecture: "Prête pour relecture",
  pret_proposition: "Prête pour proposition",
};

export const SERVICE_TYPE_LABELS: Record<string, string> = {
  transport: "Transport",
  hebergement: "Hébergement",
  activite: "Activité",
};

export const CHOICE_LABELS: Record<"keep" | "replace" | "drop", string> = {
  keep: "Garder",
  replace: "Remplacer",
  drop: "Retirer",
};

export type ProposalAction = "accepter" | "demander_correction" | "refuser";

export const PROPOSAL_ACTION_LABELS: Record<ProposalAction, string> = {
  accepter: "Valider et envoyer au voyageur",
  demander_correction: "Demander une correction",
  refuser: "Refuser",
};

/** Statuses in which the advisor may still edit a proposal before sending it. */
export const EDITABLE_STATUSES = new Set(["brouillon", "correction_requested"]);

/** Who holds the proposal now, said plainly: the agent never sends or confirms. */
export const PROPOSAL_STAGE: Record<string, string> = {
  brouillon: "Brouillon préparé par l'assistant · non envoyé",
  correction_requested: "Correction demandée · non envoyé",
  envoyee: "Envoyée au voyageur · en attente de sa réponse",
  validee: "Validée · rien n'est réservé pour l'instant",
  refusee: "Refusée",
};

function parseDay(value: string): Date | null {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return null;
  const day = new Date(`${value}T12:00:00`);
  return isNaN(day.getTime()) ? null : day;
}

/** "2026-11-07" -> "sam. 7 nov. 2026". */
export function formatDay(value: string): string {
  const day = parseDay(value);
  if (!day) return value || "—";
  return day.toLocaleDateString("fr-FR", {
    weekday: "short",
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

/** Number of nights between two YYYY-MM-DD dates, or null if unknown. */
export function countNights(departure: string, back: string): number | null {
  const start = parseDay(departure);
  const end = parseDay(back);
  if (!start || !end) return null;
  return Math.round((end.getTime() - start.getTime()) / 86_400_000);
}

/** ISO timestamp -> "22/10 à 09:40", in the viewer's time zone. */
export function formatCheckedAt(iso: string | null | undefined): string {
  if (!iso) return "";
  const moment = new Date(iso);
  if (isNaN(moment.getTime())) return "";
  const day = moment.toLocaleDateString("fr-FR", { day: "2-digit", month: "2-digit" });
  const time = moment.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
  return `${day} à ${time}`;
}
