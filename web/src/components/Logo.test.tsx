import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import { Logo } from "./Logo";
import { LOGO_VIEWBOX, MONOGRAMME_VIEWBOX } from "./logoPaths";

/** The raw stylesheet: the animation and 96 px swap tokens live in CSS. */
const css = readFileSync(join(process.cwd(), "src", "index.css"), "utf8");

/*
 * Logo contract (tickets #132 #198, charte 2026):
 * - one component, four charte variants (encre, negatif, mono-encre, mono-blanc);
 * - the O rises half a capital and stays yellow (encre / negatif);
 * - below 96 px of the REAL rendered width, the DO monogramme replaces the
 *   wordmark, and reverses when space comes back (CSS container query, no JS);
 * - the jumping o plays once (app open / advisor confirmation), never at rest;
 * - reduced motion renders the logo static (index.css media rule).
 */

interface LogoPieces {
  slot: HTMLElement;
  wordmark: HTMLElement;
  do: HTMLElement;
}

function pieces(container: HTMLElement): LogoPieces {
  return {
    slot: container.querySelector(".logo-slot") as HTMLElement,
    wordmark: container.querySelector('[data-logo="wordmark"]') as HTMLElement,
    do: container.querySelector('[data-logo="do"]') as HTMLElement,
  };
}

describe("Logo variants", () => {
  it("renders the ink variant by default, on the wordmark and the shared geometry", () => {
    const view = render(<Logo />);
    const { slot, wordmark, do: doSvg } = pieces(view.container);
    expect(slot).toBeInTheDocument();
    expect(wordmark).toHaveClass("logo", "logo-encre");
    expect(wordmark).toHaveAttribute("viewBox", LOGO_VIEWBOX);
    expect(doSvg).toHaveAttribute("viewBox", MONOGRAMME_VIEWBOX);
    expect(doSvg).toHaveClass("logo", "logo-encre");
  });

  it.each([
    ["encre", "logo-encre"],
    ["negatif", "logo-negatif"],
    ["mono-encre", "logo-mono-encre"],
    ["mono-blanc", "logo-mono-blanc"],
  ] as const)("maps variant %s to class %s on both glyphs", (variant, expected) => {
    const view = render(<Logo variant={variant} />);
    const { wordmark, do: doSvg } = pieces(view.container);
    expect(wordmark).toHaveClass("logo", expected);
    expect(doSvg).toHaveClass("logo", expected);
  });

  it("carries the accessible label on the wordmark and keeps the DO decorative", () => {
    const view = render(<Logo label="Marque DÉTOUR" />);
    const { wordmark, do: doSvg } = pieces(view.container);
    expect(wordmark).toHaveAttribute("aria-label", "Marque DÉTOUR");
    expect(doSvg).toHaveAttribute("aria-hidden", "true");
  });

  it("draws the baseline letters and the raised o (kit half-capital lift)", () => {
    const view = render(<Logo />);
    const { wordmark, do: doSvg } = pieces(view.container);
    for (const svg of [wordmark, doSvg]) {
      expect(svg.querySelector("path.rest")).not.toBeNull();
      const oGroup = svg.querySelector("g.o-move");
      expect(oGroup).not.toBeNull();
      // The o group sits inside a translate that lifts it half a capital.
      const lifted = oGroup?.closest("g[transform]");
      expect(lifted).not.toBeNull();
      expect(lifted?.getAttribute("transform")).toContain("-330");
    }
  });
});

describe("Logo 96 px rule", () => {
  it("sizes the slot exactly when an explicit width is given", () => {
    const view = render(<Logo width={112} />);
    const { slot } = pieces(view.container);
    expect(slot).toHaveStyle({ width: "112px" });
  });

  it("renders only the DO monogramme below 96 px of explicit width", () => {
    const view = render(<Logo width={80} />);
    const monogram = view.container.querySelector('[data-logo="monogram"]');
    expect(monogram).toHaveAttribute("viewBox", MONOGRAMME_VIEWBOX);
    expect(view.container.querySelector('[data-logo="wordmark"]')).toBeNull();
  });

  it("renders the full wordmark from 96 px up, with both glyphs in the slot", () => {
    for (const width of [96, 112, 128]) {
      const view = render(<Logo width={width} />);
      const { wordmark, do: doSvg } = pieces(view.container);
      expect(wordmark).toHaveAttribute("viewBox", LOGO_VIEWBOX);
      expect(doSvg).toBeInTheDocument();
      view.unmount();
    }
  });

  it("lets the container query enforce the swap on the real rendered width", () => {
    // The swap is decided by the slot's real width (CSS): reacts to squeezes
    // and reverses when space returns - the charter swap of #198.
    const flat = css.replace(/\s+/g, " ");
    expect(css).toContain(".logo-slot");
    expect(css).toContain("container-type: inline-size");
    expect(css).toContain("@container (width < 96px)");
    expect(flat).toContain(
      "@container (width < 96px) { .logo-slot .logo-wordmark { display: none; }",
    );
    expect(flat).toContain(".logo-slot .logo-do { display: block; width: 44px; height: 44px; }");
  });

  it("prices the surfaces that use the wordmark at 96 px or more", () => {
    // Public nav and login pass explicit 112 px slots (>= 96, charter wordmark);
    // the footer passes 128 and the hero relies on its fixed w-56 (224 px).
    const sources = [
      ["src/components/landing/PublicNav.tsx", "width={112}"],
      ["src/components/landing/Footer.tsx", "width={128}"],
      ["src/pages/Login.tsx", "width={112}"],
    ];
    for (const [file, needle] of sources) {
      const source = readFileSync(join(process.cwd(), file), "utf8");
      expect(source.includes(needle), `${file} loses the ${needle} charter slot`).toBe(true);
    }
    const hero = readFileSync(join(process.cwd(), "src/components/landing/Hero.tsx"), "utf8");
    expect(hero).toContain("w-56");
  });
});

describe("Logo confirmation animation", () => {
  it("stays at rest without the play prop", () => {
    const view = render(<Logo />);
    const { wordmark, do: doSvg } = pieces(view.container);
    expect(wordmark).not.toHaveClass("play");
    expect(doSvg).not.toHaveClass("play");
  });

  it("plays the jumping o exactly when play is requested", () => {
    const view = render(<Logo play />);
    const { wordmark, do: doSvg } = pieces(view.container);
    expect(wordmark).toHaveClass("play");
    expect(doSvg).toHaveClass("play");
  });

  it("starts playing when play arrives after the first render", () => {
    const view = render(<Logo />);
    const { wordmark } = pieces(view.container);
    expect(wordmark).not.toHaveClass("play");
    view.rerender(<Logo play />);
    expect(view.container.querySelector('[data-logo="wordmark"]')).toHaveClass("play");
  });
});

describe("Reduced motion contract (index.css)", () => {
  it("runs the jumping o once, on the charte curve", () => {
    expect(css).toContain("-animate-saut: saut 1150ms cubic-bezier(0.3, 0.7, 0.4, 1) both");
  });

  it("disables the animation under prefers-reduced-motion", () => {
    const reduced = css.slice(css.lastIndexOf("@media (prefers-reduced-motion: reduce)"));
    expect(reduced).toContain(".play .o-move");
    expect(reduced).toContain("animation: none");
  });
});
