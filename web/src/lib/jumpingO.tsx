import { jumpO } from "./jumpingOHelpers";

/*
 * Jumping o — branded typographic gesture (see brand-2026/charte/index.html).
 *
 * Rules enforced here:
 * - Only one o per composition may jump (one target word per title).
 * - The jumping o is yellow (class .j, color: var(--color-yellow)).
 * - It is raised by half a capital height (top: -.264em).
 * - Only titles and hooks of at least 28px use it — callers decide placement.
 * - Never applied to prices, dates or addresses (no such input is accepted).
 */

interface JumpingTitleProps {
  /** Title text; must be a plain string (no prices, dates or addresses). */
  text: string;
  /** The word carrying the main idea; its first "o" jumps. */
  targetWord: string;
  /** Heading level rendered. Defaults to "h2". */
  as?: "h1" | "h2" | "h3" | "h4";
  className?: string;
}

/**
 * Title rendering helper: applies the jumping o to `targetWord`.
 * Renders nothing special when the target word is absent or has no "o".
 */
export function JumpingTitle({ text, targetWord, as = "h2", className }: JumpingTitleProps) {
  const Tag = as;
  const words = text.split(" ");
  const targetIndex = words.findIndex((word) => word.toLowerCase() === targetWord.toLowerCase());
  if (targetIndex === -1) {
    return <Tag className={className}>{text}</Tag>;
  }
  return (
    <Tag className={className}>
      {words.map((word, i) => (
        <span key={i}>
          {i === targetIndex ? jumpO(word) : word}
          {i < words.length - 1 ? " " : ""}
        </span>
      ))}
    </Tag>
  );
}
