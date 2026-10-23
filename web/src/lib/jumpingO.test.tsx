import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import { JumpingTitle } from "./jumpingO";
import { firstOIndex, isPriceDateAddress, jumpO } from "./jumpingOHelpers";

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

  it("returns the word unchanged when it carries a digit or a currency mark", () => {
    for (const word of ["boîte2", "Tomate€", " coût$"]) {
      const { container } = render(<>{jumpO(word)}</>);
      expect(container.querySelector("span.j")).toBeNull();
      expect(container.textContent).toBe(word);
    }
  });
});

describe("isPriceDateAddress", () => {
  it("detects prices", () => {
    expect(isPriceDateAddress("À partir de 96 € par personne")).toBe(true);
    expect(isPriceDateAddress("Un séjour à 1200 EUR")).toBe(true);
    expect(isPriceDateAddress("Pack découverte à 89 $")).toBe(true);
  });

  it("detects dates, numeric or spelled out", () => {
    expect(isPriceDateAddress("Départ le 07/11/2026")).toBe(true);
    expect(isPriceDateAddress("Embarquement le samedi")).toBe(true);
    expect(isPriceDateAddress("Croisière de novembre")).toBe(true);
  });

  it("detects street addresses", () => {
    expect(isPriceDateAddress("Comptoir installé 12 rue des Olivettes")).toBe(true);
    expect(isPriceDateAddress("Rendez-vous 45 quai des Antilles")).toBe(true);
  });

  it("lets plain travel copy through", () => {
    expect(isPriceDateAddress("Le meilleur détour de voyage")).toBe(false);
    expect(isPriceDateAddress("Croisière de Nantes à Lisbonne")).toBe(false);
    expect(isPriceDateAddress("Un voyage complet, du train à l'hôtel")).toBe(false);
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

  it("jumps only the first o when the target word holds two", () => {
    const { container } = render(<JumpingTitle text="Bonjour la bordée" targetWord="bonjour" />);
    const spans = container.querySelectorAll("span.j");
    expect(spans).toHaveLength(1);
    expect(spans[0].textContent).toBe("o");
    expect(container.textContent).toBe("Bonjour la bordée");
  });

  it("never jumps on a price, even when the target word has an o", () => {
    const { container } = render(
      <JumpingTitle text="Croisière à partir de 120 € la nuit" targetWord="croisière" />,
    );
    expect(container.querySelector("span.j")).toBeNull();
    expect(container.textContent).toBe("Croisière à partir de 120 € la nuit");
  });

  it("never jumps on a date, even when the target word has an o", () => {
    const { container } = render(
      <JumpingTitle text="Embarquement le 07/11 à Nantes" targetWord="embarquement" />,
    );
    expect(container.querySelector("span.j")).toBeNull();
    expect(container.textContent).toBe("Embarquement le 07/11 à Nantes");
  });

  it("never jumps on a street address, even when the target word has an o", () => {
    const { container } = render(
      <JumpingTitle text="Comptoir à 12 rue Bonnenaire" targetWord="comptoir" />,
    );
    expect(container.querySelector("span.j")).toBeNull();
    expect(container.textContent).toBe("Comptoir à 12 rue Bonnenaire");
  });

  it("renders plain when the target word itself carries a digit", () => {
    const { container } = render(
      <JumpingTitle text="La formule Solo2 s'embarque" targetWord="solo2" />,
    );
    expect(container.querySelector("span.j")).toBeNull();
    expect(container.textContent).toBe("La formule Solo2 s'embarque");
  });
});
