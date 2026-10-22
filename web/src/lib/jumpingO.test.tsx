import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import { JumpingTitle } from "./jumpingO";
import { firstOIndex, jumpO } from "./jumpingOHelpers";

describe("firstOIndex", () => {
  it("finds the first o case-insensitively", () => {
    expect(firstOIndex("Détour")).toBe(3);
    expect(firstOIndex("Ombre")).toBe(0);
  });

  it("returns -1 when the word has no o", () => {
    expect(firstOIndex("train")).toBe(-1);
    expect(firstOIndex("")).toBe(-1);
  });
});

describe("jumpO", () => {
  it("wraps the first o in a jumping span", () => {
    const { container } = render(<>{jumpO("détour")}</>);
    const span = container.querySelector("span.j");
    expect(span).not.toBeNull();
    expect(span?.textContent).toBe("o");
    expect(container.textContent).toBe("détour");
  });

  it("returns the word unchanged when there is no o", () => {
    const { container } = render(<>{jumpO("train")}</>);
    expect(container.querySelector("span.j")).toBeNull();
    expect(container.textContent).toBe("train");
  });
});

describe("JumpingTitle", () => {
  it("applies exactly one jumping o to the target word", () => {
    const { container } = render(
      <JumpingTitle text="Le meilleur détour de voyage" targetWord="détour" />,
    );
    const spans = container.querySelectorAll("span.j");
    expect(spans).toHaveLength(1);
    expect(spans[0].textContent).toBe("o");
    expect(container.textContent).toBe("Le meilleur détour de voyage");
  });

  it("renders plain text when the target word is absent", () => {
    const { container } = render(<JumpingTitle text="Un voyage complet" targetWord="détour" />);
    expect(container.querySelector("span.j")).toBeNull();
    expect(container.textContent).toBe("Un voyage complet");
  });

  it("renders plain text when the target word has no o", () => {
    const { container } = render(<JumpingTitle text="Un voyage sur mesure" targetWord="mesure" />);
    expect(container.querySelector("span.j")).toBeNull();
    expect(container.textContent).toBe("Un voyage sur mesure");
  });

  it("matches the target word case-insensitively", () => {
    const { container } = render(<JumpingTitle text="Prêt pour le DÉTOUR" targetWord="détour" />);
    expect(container.querySelectorAll("span.j")).toHaveLength(1);
  });
});
