import { describe, expect, it } from "vitest";
import type { PrestationRecherche } from "../types";
import { ETAT_LABELS, etatPrestation, verificationEchouee } from "./verification";

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
