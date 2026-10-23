import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { Hero } from "./Hero";

/*
 * Ticket #182: the hero shows the 2026 brand photograph, not a fabricated
 * gradient — real <img> with alt text, no « Visuel fictif » badge.
 */

function renderHero() {
  return render(
    <MemoryRouter>
      <Hero onDecrir={() => {}} />
    </MemoryRouter>,
  );
}

describe("Hero photograph", () => {
  it("serves the brand photo with a descriptive alt", () => {
    const photo = renderHero().getByRole("img", { name: /train au couchant/i });
    expect(photo).toHaveAttribute("src", "/brand-2026/photo/train.webp");
    expect(photo.getAttribute("src")?.endsWith(".webp")).toBe(true);
  });

  it("no longer carries the fabricated-visual badge", () => {
    expect(renderHero().queryByText(/Visuel d'illustration fictif/)).toBeNull();
  });
});
