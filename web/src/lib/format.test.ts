import { describe, expect, it } from "vitest";
import { derniereConfirmation } from "./format";
import type { DecisionStatut } from "../types";

function confirmation(par: string): DecisionStatut {
  return {
    action: "accepter",
    par,
    le: "2026-10-22T10:00:00+00:00",
    motif: "prix conforme au budget",
  };
}

describe("derniereConfirmation", () => {
  it("renvoie la confirmation du conseiller", () => {
    expect(derniereConfirmation([confirmation("Conseiller DÉTOUR")])).toMatchObject({
      action: "accepter",
      par: "Conseiller DÉTOUR",
      motif: "prix conforme au budget",
    });
  });

  it("renvoie null quand aucune confirmation n'a été donnée", () => {
    expect(derniereConfirmation(undefined)).toBeNull();
    expect(derniereConfirmation([])).toBeNull();
  });

  it("ignore une correction : corriger n'est pas confirmer", () => {
    const journal = [{ ...confirmation("Conseiller DÉTOUR"), action: "demander_correction" }];
    expect(derniereConfirmation(journal)).toBeNull();
  });

  it("renvoie la dernière confirmation quand le journal en compte plusieurs", () => {
    const journal = [confirmation("Conseiller A"), confirmation("Conseiller B")];
    expect(derniereConfirmation(journal)?.par).toBe("Conseiller B");
  });
});
