/**
 * Détour Voyages tone of voice for traveler-facing text (#112).
 * Precise first: every price is dated, every seat count is a number.
 */
import type { Proposition } from "../types";

/** Default advisor names that are not a real first name. */
const NOT_A_FIRST_NAME = new Set(["", "conseiller", "conseiller détour"]);

function sameDay(a: Date, b: Date): boolean {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}

/** 9:40 -> "9 h 40", the French way. */
export function formatClock(moment: Date): string {
  return `${moment.getHours()} h ${String(moment.getMinutes()).padStart(2, "0")}`;
}

/** "ce matin à 9 h 40", "hier à 18 h 05", "le 19/10 à 9 h 40". Empty if unknown. */
export function whenChecked(iso: string | null | undefined, now: Date = new Date()): string {
  if (!iso) return "";
  const moment = new Date(iso);
  if (isNaN(moment.getTime())) return "";
  const clock = formatClock(moment);
  if (sameDay(moment, now)) {
    const hour = moment.getHours();
    const part = hour < 12 ? "ce matin" : hour < 18 ? "cet après-midi" : "ce soir";
    return `${part} à ${clock}`;
  }
  const yesterday = new Date(now);
  yesterday.setDate(now.getDate() - 1);
  if (sameDay(moment, yesterday)) return `hier à ${clock}`;
  const day = moment.toLocaleDateString("fr-FR", { day: "2-digit", month: "2-digit" });
  return `le ${day} à ${clock}`;
}

/** "Prix vérifié ce matin à 9 h 40." or "" when the check time is unknown. */
export function priceCheckedSentence(iso: string | null | undefined, now?: Date): string {
  const when = whenChecked(iso, now);
  return when ? `Prix vérifié ${when}.` : "";
}

/** "Il reste 6 places à cette date." */
export function seatsSentence(seats: number | null | undefined): string {
  if (seats === null || seats === undefined) return "";
  if (seats <= 0) return "Plus aucune place à cette date.";
  return seats === 1 ? "Il reste 1 place à cette date." : `Il reste ${seats} places à cette date.`;
}

/** 179 -> "179 €", 29.5 -> "29,50 €": no decimals when the amount is whole. */
export function formatAmount(amount: number): string {
  return new Intl.NumberFormat("fr-FR", {
    style: "currency",
    currency: "EUR",
    minimumFractionDigits: Number.isInteger(amount) ? 0 : 2,
    maximumFractionDigits: Number.isInteger(amount) ? 0 : 2,
  }).format(amount);
}

/** "179 € par personne." */
export function perPersonSentence(amount: number): string {
  return `${formatAmount(amount)} par personne.`;
}

/**
 * The advisor who signs the proposal: whoever sent it, else whoever prepared
 * it. Returns null when only a default name is known.
 */
export function advisorFirstName(proposal: Proposition): string | null {
  const sent = [...(proposal.decisions_statut ?? [])]
    .reverse()
    .find((d) => d.action === "accepter" || (d as { apres?: string }).apres === "envoyee");
  for (const name of [sent?.par, proposal.conseiller]) {
    const clean = (name ?? "").trim();
    if (!NOT_A_FIRST_NAME.has(clean.toLowerCase())) return clean;
  }
  return null;
}

/** "samedi 7 novembre". */
export function formatLongDay(value: string): string {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return value;
  const day = new Date(`${value}T12:00:00`);
  if (isNaN(day.getTime())) return value;
  return day.toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "long" });
}

/** Number of nights between two YYYY-MM-DD dates, or null. */
export function nightsBetween(departure: string, back: string): number | null {
  const start = new Date(`${departure}T12:00:00`);
  const end = new Date(`${back}T12:00:00`);
  if (isNaN(start.getTime()) || isNaN(end.getTime())) return null;
  return Math.round((end.getTime() - start.getTime()) / 86_400_000);
}
