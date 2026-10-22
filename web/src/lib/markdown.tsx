import { createElement, type ReactNode } from "react";

/**
 * Light, safe markdown subset for assistant chat replies.
 * Zero deps — escapes HTML, no images, no raw HTML passthrough.
 *
 * Supports: paragraphs, soft line breaks, **bold**, *italic*, `code`,
 * unordered (- / *) and ordered (1.) lists.
 */

const INLINE_PATTERN =
  /(\*\*[^*\n]+?\*\*|\*[^*\n]+?\*|`[^`\n]+?`|\[([^\]]+)\]\((https?:\/\/[^)\s]+)\))/g;

function renderInline(text: string, keyPrefix: string): ReactNode[] {
  const nodes: ReactNode[] = [];
  let last = 0;
  let match: RegExpExecArray | null;
  let i = 0;
  // Fresh regex per call: a shared /g lastIndex breaks under recursion.
  const re = new RegExp(INLINE_PATTERN.source, "g");

  while ((match = re.exec(text)) !== null) {
    if (match.index > last) {
      nodes.push(text.slice(last, match.index));
    }
    const token = match[0];
    const key = `${keyPrefix}-${i++}`;

    if (token.startsWith("**") && token.endsWith("**")) {
      nodes.push(createElement("strong", { key }, token.slice(2, -2)));
    } else if (token.startsWith("*") && token.endsWith("*")) {
      nodes.push(createElement("em", { key }, token.slice(1, -1)));
    } else if (token.startsWith("`") && token.endsWith("`")) {
      nodes.push(
        createElement(
          "code",
          { key, className: "rounded bg-ink/8 px-1 py-0.5 font-mono text-[0.9em]" },
          token.slice(1, -1),
        ),
      );
    } else if (match[2] !== undefined && match[3] !== undefined) {
      // [label](https://…) — http(s) only (captured by the regex).
      nodes.push(
        createElement(
          "a",
          {
            key,
            href: match[3],
            target: "_blank",
            rel: "noopener noreferrer",
            className: "underline underline-offset-2",
          },
          match[2],
        ),
      );
    } else {
      nodes.push(token);
    }
    last = match.index + token.length;
  }

  if (last < text.length) {
    nodes.push(text.slice(last));
  }
  return nodes;
}

type Block =
  | { type: "p"; lines: string[] }
  | { type: "ul"; items: string[] }
  | { type: "ol"; items: string[] };

function parseBlocks(source: string): Block[] {
  const lines = source.replace(/\r\n?/g, "\n").split("\n");
  const blocks: Block[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    if (line.trim() === "") {
      i += 1;
      continue;
    }

    const ul = /^(?:[-*])\s+(.+)$/.exec(line);
    if (ul) {
      const items: string[] = [ul[1]];
      i += 1;
      while (i < lines.length) {
        const next = /^(?:[-*])\s+(.+)$/.exec(lines[i]);
        if (!next) break;
        items.push(next[1]);
        i += 1;
      }
      blocks.push({ type: "ul", items });
      continue;
    }

    const ol = /^(\d+)\.\s+(.+)$/.exec(line);
    if (ol) {
      const items: string[] = [ol[2]];
      i += 1;
      while (i < lines.length) {
        const next = /^(\d+)\.\s+(.+)$/.exec(lines[i]);
        if (!next) break;
        items.push(next[2]);
        i += 1;
      }
      blocks.push({ type: "ol", items });
      continue;
    }

    const para: string[] = [line];
    i += 1;
    while (i < lines.length && lines[i].trim() !== "") {
      if (/^(?:[-*]|\d+\.)\s+/.test(lines[i])) break;
      para.push(lines[i]);
      i += 1;
    }
    blocks.push({ type: "p", lines: para });
  }

  return blocks;
}

/** Render a safe markdown subset as React nodes (text is never injected as HTML). */
export function renderLightMarkdown(source: string): ReactNode {
  if (!source) return null;

  const blocks = parseBlocks(source);
  if (blocks.length === 0) return null;

  return blocks.map((block, bi) => {
    if (block.type === "ul") {
      return createElement(
        "ul",
        { key: `ul-${bi}`, className: "my-1 list-disc space-y-0.5 pl-5" },
        block.items.map((item, ii) =>
          createElement("li", { key: `uli-${bi}-${ii}` }, renderInline(item, `uli-${bi}-${ii}`)),
        ),
      );
    }
    if (block.type === "ol") {
      return createElement(
        "ol",
        { key: `ol-${bi}`, className: "my-1 list-decimal space-y-0.5 pl-5" },
        block.items.map((item, ii) =>
          createElement("li", { key: `oli-${bi}-${ii}` }, renderInline(item, `oli-${bi}-${ii}`)),
        ),
      );
    }

    // Paragraph: soft line breaks between lines.
    const children: ReactNode[] = [];
    block.lines.forEach((line, li) => {
      if (li > 0) children.push(createElement("br", { key: `br-${bi}-${li}` }));
      children.push(...renderInline(line, `p-${bi}-${li}`));
    });
    return createElement(
      "p",
      { key: `p-${bi}`, className: bi === 0 ? undefined : "mt-2" },
      children,
    );
  });
}
