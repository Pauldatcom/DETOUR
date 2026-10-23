import { describe, expect, it } from "vitest";
import type { ChangementLecture, Prestation, PrestationRecherche } from "../types";
import {
  ETAT_LABELS,
  dateVerificationValide,
  etatPrestation,
  etatTarifVoyageur,
  verificationEchouee,
} from "./verification";

const AT = "2026-10-22T07:40:00+00:00";

function result(extra: Partial<PrestationRecherche> = {}): PrestationRecherche {
  return {
    id: "hotel-lyon-01",
    nom: "Hôtel des Lumières",
    type: "hebergement",
    destination: "Lyon",
    prix_unitaire_eur: 88,
    prix_total_eur: 176,
    disponible: true,
    dans_budget: true,
    ...extra,
  };
}

describe("etatPrestation", () => {
  it("is verified with a price, availability and a check time", () => {
    expect(etatPrestation(result(), AT)).toBe("verified");
  });

  it("is not verified without a check time or a price", () => {
    expect(etatPrestation(result(), null)).toBe("not_verified");
    expect(etatPrestation(result({ prix_unitaire_eur: undefined as unknown as number }), AT)).toBe(
      "not_verified",
    );
  });

  it("is never available when the server says it is not", () => {
    expect(etatPrestation(result({ disponible: false }), AT)).toBe("unavailable");
    expect(
      etatPrestation(result({ disponible: false }), AT, result({ prix_unitaire_eur: 70 })),
    ).toBe("unavailable");
  });

  it("is modified when the price changed since an earlier reading", () => {
    expect(etatPrestation(result(), AT, result({ prix_unitaire_eur: 80 }))).toBe("modified");
    expect(etatPrestation(result(), AT, result())).toBe("verified");
  });
});

function prestation(extra: Partial<Prestation> = {}): Prestation {
  return {
    id: "hotel-lyon-01",
    nom: "Hôtel des Lumières",
    type: "hebergement",
    quantite: 2,
    verification: "verifie",
    prix_unitaire_eur: 88,
    prix_total_eur: 176,
    disponible: true,
    source: "Serveur fictif DÉTOUR",
    consulte_le: AT,
    ...extra,
  };
}

function changement(extra: Partial<ChangementLecture> = {}): ChangementLecture {
  return {
    id: "hotel-lyon-01",
    nom: "Hôtel des Lumières",
    prix_avant: 88,
    prix_apres: 96,
    disponible_avant: true,
    disponible_apres: true,
    prix_change: true,
    disponibilite_change: false,
    inchange: false,
    consulte_le: "2026-10-23T08:30:00+00:00",
    ...extra,
  };
}

describe("etatTarifVoyageur", () => {
  it("confirms a price only with an amount and a valid check date", () => {
    expect(etatTarifVoyageur(prestation())).toBe("verified");
    expect(etatTarifVoyageur(prestation({ consulte_le: null }))).toBe("not_verified");
    expect(etatTarifVoyageur(prestation({ consulte_le: "not-a-date" }))).toBe("not_verified");
    expect(etatTarifVoyageur(prestation({ prix_unitaire_eur: null }))).toBe("not_verified");
    expect(etatTarifVoyageur(prestation({ verification: "manquant" }))).toBe("not_verified");
  });

  it("keeps a price copied from v1 in checking, never verified", () => {
    expect(etatTarifVoyageur(prestation({ copie_depuis_v1: true }))).toBe("checking");
  });

  it("flags a dated price change as modified and refuses an undated one", () => {
    expect(etatTarifVoyageur(prestation(), changement())).toBe("modified");
    expect(etatTarifVoyageur(prestation(), changement({ consulte_le: null }))).toBe("checking");
  });

  it("reports availability from the latest reading", () => {
    expect(etatTarifVoyageur(prestation({ disponible: false }))).toBe("unavailable");
    expect(
      etatTarifVoyageur(
        prestation(),
        changement({
          prix_change: false,
          prix_apres: 88,
          disponibilite_change: true,
          disponible_apres: false,
        }),
      ),
    ).toBe("unavailable");
    expect(
      etatTarifVoyageur(
        prestation({ disponible: false }),
        changement({
          prix_change: false,
          prix_apres: 88,
          disponibilite_change: true,
          disponible_apres: true,
        }),
      ),
    ).toBe("verified");
  });
});

describe("dateVerificationValide", () => {
  it("accepts a real ISO date and rejects empty or invalid values", () => {
    expect(dateVerificationValide(AT)).toBe(true);
    expect(dateVerificationValide(null)).toBe(false);
    expect(dateVerificationValide("")).toBe(false);
    expect(dateVerificationValide("nope")).toBe(false);
  });
});

describe("verificationEchouee", () => {
  it("flags a server error, not a refused or successful call", () => {
    expect(verificationEchouee([{ outil: "verifier_prestations", statut: "ok" }])).toBe(false);
    expect(verificationEchouee([{ outil: "x", statut: "refuse" }])).toBe(false);
    expect(
      verificationEchouee([{ outil: "verifier_prestations", statut: "serveur_indisponible" }]),
    ).toBe(true);
    expect(verificationEchouee(undefined)).toBe(false);
  });
});

it("has a French label for each of the six states", () => {
  expect(Object.keys(ETAT_LABELS).sort()).toEqual(
    ["checking", "error", "modified", "not_verified", "unavailable", "verified"].sort(),
  );
});
