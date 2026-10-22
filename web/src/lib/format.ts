export const STATUT_LABELS: Record<string, string> = {
  nouvelle: "Nouvelle",
  a_analyser: "À analyser",
  a_revoir: "À revoir",
  repondue: "Répondue",
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

/*
 * Status text colors — 2026 brand palette.
 * Yellow is never used as text on a light background (charte rule),
 * so accent states fall back to ink; corrections use brick.
 */
export const STATUT_COLORS: Record<string, string> = {
  nouvelle: "text-ballast",
  a_analyser: "text-ballast",
  a_revoir: "text-brick",
  repondue: "text-ink",
  propose: "text-ink",
  valide: "text-ink",
  refuse: "text-brick",
  brouillon: "text-muted",
  envoyee: "text-ink",
  validee: "text-ink",
  refusee: "text-brick",
  correction_requested: "text-brick",
};

export function formatEuro(value: number): string {
  return new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR" }).format(value);
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
