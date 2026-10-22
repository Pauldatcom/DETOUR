import { describe, expect, it } from "vitest";
import type { Proposition } from "../types";
import {
  advisorFirstName,
  formatLongDay,
  nightsBetween,
  perPersonSentence,
  priceCheckedSentence,
  seatsSentence,
  whenChecked,
} from "./tone";

// Local-time timestamps keep the tests independent from the machine time zone.
const NOW = new Date(2026, 9, 22, 15, 0);
const at = (day: number, hour: number, minute: number) =>
  new Date(2026, 9, day, hour, minute).toISOString();

function proposal(extra: Partial<Proposition> = {}): Proposition {
  return {
    id: "prop_1",
    demande_id: "dem_1",
    statut: "envoyee",
    cree_le: "",
    modifiee_le: "",
    conseiller: "",
    titre: "",
    description: "",
    prestations: [],
    prix_total_eur: 0,
    ...extra,
  };
}

describe("whenChecked", () => {
  it("says this morning, this afternoon or this evening for today", () => {
    expect(whenChecked(at(22, 9, 40), NOW)).toBe("ce matin à 9 h 40");
    expect(whenChecked(at(22, 14, 5), NOW)).toBe("cet après-midi à 14 h 05");
    expect(whenChecked(at(22, 19, 0), NOW)).toBe("ce soir à 19 h 00");
  });

  it("says yesterday, then the date", () => {
    expect(whenChecked(at(21, 18, 5), NOW)).toBe("hier à 18 h 05");
    expect(whenChecked(at(19, 9, 40), NOW)).toBe("le 19/10 à 9 h 40");
  });

  it("returns nothing when the time is unknown", () => {
    expect(whenChecked(null, NOW)).toBe("");
    expect(whenChecked("pas une date", NOW)).toBe("");
  });
});

describe("sentences", () => {
  it("dates every price", () => {
    expect(priceCheckedSentence(at(22, 9, 40), NOW)).toBe("Prix vérifié ce matin à 9 h 40.");
    expect(priceCheckedSentence(null, NOW)).toBe("");
  });

  it("gives the price per person without needless decimals", () => {
    expect(perPersonSentence(179).replace(/\s/g, " ")).toBe("179 € par personne.");
    expect(perPersonSentence(29.5).replace(/\s/g, " ")).toBe("29,50 € par personne.");
  });

  it("counts the seats left", () => {
    expect(seatsSentence(6)).toBe("Il reste 6 places à cette date.");
    expect(seatsSentence(1)).toBe("Il reste 1 place à cette date.");
    expect(seatsSentence(0)).toBe("Plus aucune place à cette date.");
    expect(seatsSentence(null)).toBe("");
  });

  it("writes dates and nights in full", () => {
    expect(formatLongDay("2026-11-07")).toBe("samedi 7 novembre");
    expect(nightsBetween("2026-11-07", "2026-11-09")).toBe(2);
  });
});

describe("advisorFirstName", () => {
  it("signs with the advisor who sent the proposal", () => {
    const sent = proposal({
      conseiller: "Alice",
      decisions_statut: [{ action: "accepter", par: "Camille", le: "" }],
    });
    expect(advisorFirstName(sent)).toBe("Camille");
  });

  it("falls back to the advisor who prepared it", () => {
    expect(advisorFirstName(proposal({ conseiller: "Alice" }))).toBe("Alice");
  });

  it("never signs with a default name", () => {
    const anonymous = proposal({
      conseiller: "Conseiller DÉTOUR",
      decisions_statut: [{ action: "accepter", par: "conseiller", le: "" }],
    });
    expect(advisorFirstName(anonymous)).toBeNull();
  });
});
