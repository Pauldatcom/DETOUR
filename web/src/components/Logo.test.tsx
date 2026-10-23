import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import { Logo } from "./Logo";
import { LOGO_VIEWBOX, MONOGRAMME_VIEWBOX } from "./logoPaths";

/** The raw stylesheet: the animation tokens live in CSS, not in the component. */
const css = readFileSync(join(process.cwd(), "src", "index.css"), "utf8");

/*
 * Logo contract (ticket #132, charte 2026):
 * - one component, four charte variants (encre, negatif, mono-encre, mono-blanc);
 * - below 96 px of available width, the DO monogramme replaces the wordmark;
 * - the jumping o plays once (app open / advisor confirmation), never at rest;
 * - reduced motion renders the logo static (index.css media rule).
 */

function logo(label = "DÉTOUR") {
  return render(<Logo />).getByRole("img", { name: label });
}

describe("Logo variants", () => {
  it("renders the ink variant by default", () => {
    expect(logo()).toHaveClass("logo", "logo-encre");
  });

  it.each([
    ["encre", "logo-encre"],
    ["negatif", "logo-negatif"],
    ["mono-encre", "logo-mono-encre"],
    ["mono-blanc", "logo-mono-blanc"],
  ] as const)("maps variant %s to class %s", (variant, expected) => {
    const svg = render(<Logo variant={variant} />).getByRole("img", { name: "DÉTOUR" });
    expect(svg).toHaveClass("logo", expected);
  });

  it("keeps the accessible label overridable", () => {
    const svg = render(<Logo label="Marque DÉTOUR" />).getByRole("img", {
      name: "Marque DÉTOUR",
    });
    expect(svg).toBeInTheDocument();
  });
});

describe("Logo size", () => {
  it("renders the DO monogramme below 96 px", () => {
    const svg = render(<Logo width={80} />).getByRole("img", { name: "DÉTOUR" });
    expect(svg).toHaveAttribute("viewBox", MONOGRAMME_VIEWBOX);
  });

  it("renders the full wordmark at 96 px and above", () => {
    for (const width of [96, 112, 128]) {
      const view = render(<Logo width={width} />);
      expect(view.getByRole("img", { name: "DÉTOUR" })).toHaveAttribute("viewBox", LOGO_VIEWBOX);
      view.unmount();
    }
  });

  it("renders the full wordmark when no width hint is given", () => {
    expect(logo()).toHaveAttribute("viewBox", LOGO_VIEWBOX);
  });

  it("draws the baseline letters, the raised o, and the monogramme d", () => {
    for (const props of [{}, { width: 80 }]) {
      const view = render(<Logo {...props} />);
      const svg = view.getByRole("img", { name: "DÉTOUR" });
      expect(svg.querySelector("path.rest")).not.toBeNull();
      expect(svg.querySelector("g.o-move path.o-fill")).not.toBeNull();
      view.unmount();
    }
  });
});

describe("Logo confirmation animation", () => {
  it("stays at rest without the play prop", () => {
    expect(logo()).not.toHaveClass("play");
  });

  it("plays the jumping o exactly when play is requested", () => {
    const svg = render(<Logo play />).getByRole("img", { name: "DÉTOUR" });
    expect(svg).toHaveClass("play");
  });

  it("starts playing when play arrives after the first render", () => {
    const { rerender, getByRole } = render(<Logo />);
    const svg = getByRole("img", { name: "DÉTOUR" });
    expect(svg).not.toHaveClass("play");
    rerender(<Logo play />);
    expect(svg).toHaveClass("play");
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
