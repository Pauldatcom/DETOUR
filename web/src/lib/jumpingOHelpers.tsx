import type { ReactNode } from "react";

/*
 * Jumping o — pure helpers (see brand-2026/charte/index.html).
 *
 * Rules enforced here:
 * - Only one o per composition may jump (one target word per title).
 * - The jumping o is yellow (class .j, color: var(--color-yellow)).
 * - It is raised by half a capital height (top: -.264em).
 * - Only titles and hooks of at least 28px use it — callers decide placement.
 * - Never applied to prices, dates or addresses (no such input is accepted).
 */

/** Return the index of the first "o" in `word` (case-insensitive), or -1. */
export function firstOIndex(word: string): number {
  return word.toLowerCase().indexOf("o");
}

/**
 * Split `word` into text nodes, wrapping its first "o" in the jumping span.
 * If the word has no "o", the word is returned unchanged.
 */
export function jumpO(word: string): ReactNode {
  const oIndex = firstOIndex(word);
  if (oIndex === -1) return word;
  return (
    <>
      {word.slice(0, oIndex)}
      <span className="j">{word[oIndex]}</span>
      {word.slice(oIndex + 1)}
    </>
  );
}
