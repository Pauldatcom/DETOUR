import type { DecisionStatut } from "../types";

export const STATUT_LABELS: Record<string, string> = {
  nouvelle: "Nouvelle",
  a_analyser: "À analyser",
  a_revoir: "À revoir",
  propose: "Proposée",
  valide: "Validée",
  refuse: "Refusée",
};

export const PROP_STATUT_LABELS: Record<string, string> = {
  brouillon: "Brouillon",
  envoyee: "Envoyée",
  validee: "Validée",
  refusee: "Refusée",
  correction_requested: "Correction demandée",
};

export const STATUT_COLORS: Record<string, string> = {
  nouvelle: "text-accent-bright",
  a_analyser: "text-warning",
  a_revoir: "text-warning",
  propose: "text-accent",
  valide: "text-success",
  refuse: "text-danger",
  brouillon: "text-muted",
  envoyee: "text-accent",
  validee: "text-success",
  refusee: "text-danger",
  correction_requested: "text-warning",
};

export function formatEuro(value: number): string {
  return new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR" }).format(value);
}

/**
 * Last advisor confirmation of a proposal, if any (#113).
 * The advisor confirms explicitly: the traveler sees who confirmed, when,
 * and why. A proposal the agent only drafted has no confirmation yet.
 */
export function derniereConfirmation(decisions?: DecisionStatut[]): DecisionStatut | null {
  if (!decisions) return null;
  for (let i = decisions.length - 1; i >= 0; i -= 1) {
    if (decisions[i].action === "accepter") return decisions[i];
  }
  return null;
}

export function formatDate(iso: string): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("fr-FR", { day: "2-digit", month: "short", year: "numeric" });
}

export function formatDateTime(iso: string): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  return d.toLocaleString("fr-FR", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}
