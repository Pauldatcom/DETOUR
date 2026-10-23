import type { ReactNode } from "react";

/*
 * Jumping o — pure helpers (see brand-2026/charte/index.html).
 *
 * Rules enforced here:
 * - Only one o per composition may jump (one target word per title).
 * - The jumping o is yellow (class .j, color: var(--color-yellow)).
 * - It is raised by half a capital height (top: -.264em).
 * - Only titles and hooks of at least 28px use it — callers decide placement.
 * - Never applied to prices, dates or addresses (see isPriceDateAddress below).
 */

/** Return the index of the first "o" in `word` (case-insensitive), or -1. */
export function firstOIndex(word: string): number {
  return word.toLowerCase().indexOf("o");
}

/*
 * The jumping o is a marketing gesture: it never carries facts. A price, a
 * date or an address renders plain (charte: "jamais sur un prix, une date,
 * une adresse"). The guards below detect each of the three.
 */

/** A currency amount somewhere in the text ("96 €", "EUR 120,50", "89 $"). */
const PATTERN_PRIX = /\d[\d\s.,]*\s?(?:€|\$|\b(?:EUR|USD)\b)/i;

/** A calendar date: numeric (07/11/2026) or spelled out (samedi 7 novembre). */
const PATTERN_DATE =
  /\b(?:\d{1,2}[/.-]\d{1,2}(?:[/.-]\d{2,4})?|lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche|janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\b/i;

/** A street address: a number followed by a road word in the same clause. */
const PATTERN_ADRESSE =
  /\b\d+\b[^.?!,]*\b(?:rue|avenue|boulevard|bd|route|place|quai|chemin|impasse|allée)\b/i;

/**
 * True when the text carries a price, a date or an address: the jumping o
 * then stays off the whole composition, even if a target word holds an o.
 */
export function isPriceDateAddress(text: string): boolean {
  return PATTERN_PRIX.test(text) || PATTERN_DATE.test(text) || PATTERN_ADRESSE.test(text);
}

/**
 * Split `word` into text nodes, wrapping its first "o" in the jumping span.
 * If the word has no "o", or carries a digit or currency mark (a price or
 * an address fragment), the word is returned unchanged.
 */
export function jumpO(word: string): ReactNode {
  const oIndex = firstOIndex(word);
  if (oIndex === -1 || /\d|[€$]/u.test(word)) return word;
  return (
    <>
      {word.slice(0, oIndex)}
      <span className="j">{word[oIndex]}</span>
      {word.slice(oIndex + 1)}
    </>
  );
}
