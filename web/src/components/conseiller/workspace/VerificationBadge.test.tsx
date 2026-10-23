import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, within, type RenderResult } from "@testing-library/react";
import { ServicesTable, type ServiceRow } from "./ServicesTable";
import { ProposalReview } from "./ProposalReview";
import type { Proposition } from "../../../types";

vi.mock("../../../lib/api", () => ({
  api: {
    decisionsPrestation: vi.fn(),
    patchProposition: vi.fn(),
  },
}));

/*
 * Verification states (ticket #132, charte 2026): a server-checked proposal
 * shows five states — four on the Vérification column (Vérifié, Repris de la
 * v1, Prix modifié, Non vérifié) plus the disponibilité cell, in Brick when
 * the service is no longer available. Prices are never footnoted: the check
 * date travels inline inside the badge.
 */

const CHECKED_AT = "2026-10-22T09:40:00+00:00";

const ROWS: ServiceRow[] = [
  {
    id: "atelier-machines-01",
    name: "Atelier des Machines",
    type: "activite",
    unitPrice: 12,
    groupTotal: 36,
    seatsLeft: 20,
    available: true,
    checkedAt: CHECKED_AT,
    state: "verified",
  },
  {
    id: "train-nantes-01",
    name: "Train vers Nantes",
    type: "transport",
    unitPrice: 96,
    groupTotal: 288,
    seatsLeft: 6,
    available: true,
    checkedAt: null,
    state: "copied",
  },
  {
    id: "hotel-nantes-01",
    name: "Hôtel des Machines",
    type: "hebergement",
    unitPrice: 110,
    groupTotal: 330,
    seatsLeft: 4,
    available: false,
    checkedAt: CHECKED_AT,
    state: "changed",
  },
  {
    id: "croisiere-erdre-01",
    name: "Croisière sur l'Erdre",
    type: "activite",
    unitPrice: null,
    groupTotal: null,
    seatsLeft: null,
    available: null,
    checkedAt: null,
    state: "unverified",
  },
];

function renderTable(): RenderResult {
  return render(<ServicesTable rows={ROWS} caption="Prestations de la proposition prop_1" />);
}

describe("VerificationBadge — the five states", () => {
  let view: RenderResult;

  beforeEach(() => {
    view = renderTable();
  });

  const rowOf = (name: string) => view.getByText(name).closest("tr")!;

  it("shows Vérifié with the inline check date, in Encre on Sky", () => {
    const badge = within(rowOf("Atelier des Machines")).getByText(
      /^Vérifié le \d{2}\/\d{2} à \d{2}:\d{2}$/,
    );
    expect(badge).toHaveClass("text-ink");
    expect(badge).not.toHaveClass("text-brick");
  });

  it("shows the v1 copy as Repris de la v1 · non relu, in Brick outline", () => {
    const badge = within(rowOf("Train vers Nantes")).getByText("Repris de la v1 · non relu");
    expect(badge).toHaveClass("text-brick");
    expect(badge).not.toHaveClass("bg-brick/10");
  });

  it("shows the modified price or availability in Brick", () => {
    const badge = within(rowOf("Hôtel des Machines")).getByText("Prix ou disponibilité modifiés");
    expect(badge).toHaveClass("text-brick", "border-brick", "bg-brick/10");
  });

  it("shows the unverified service as Non vérifié, in Ballast", () => {
    const badge = within(rowOf("Croisière sur l'Erdre")).getByText("Non vérifié");
    expect(badge).toHaveClass("text-ballast");
  });

  it("paints the disponibilité cell in Brick when the service is gone", () => {
    const gone = within(rowOf("Hôtel des Machines")).getByText("Indisponible");
    expect(gone).toHaveClass("text-brick", "font-medium");

    const open = within(rowOf("Atelier des Machines")).getByText("Disponible");
    expect(open).not.toHaveClass("text-brick");

    expect(within(rowOf("Croisière sur l'Erdre")).getByText("Non vérifiée")).toBeInTheDocument();
  });
});

describe("VerificationBadge — no footnotes", () => {
  it("never uses asterisks, daggers or superscripts; dates stay inline", () => {
    const { container } = renderTable();
    expect(container).not.toHaveTextContent(/[*†]/);
    expect(container).not.toHaveTextContent(/[\u00B9\u00B2\u00B3]/);
  });
});

describe("ProposalReview — modified price in Brick", () => {
  it("renders the new price of a changed service in Brick", () => {
    const proposal = {
      id: "prop_1",
      demande_id: "dem_1",
      statut: "brouillon",
      cree_le: "2026-10-22T08:00:00+00:00",
      modifiee_le: "2026-10-22T08:00:00+00:00",
      conseiller: "",
      titre: "Nantes en famille",
      description: "Deux jours au calme.",
      prix_total_eur: 288,
      prestations: [
        {
          id: "hotel-nantes-01",
          nom: "Hôtel des Machines",
          type: "hebergement",
          quantite: 3,
          verification: "verifie",
          prix_unitaire_eur: 96,
          prix_total_eur: 288,
          disponible: true,
          source: "Serveur fictif DÉTOUR",
          consulte_le: CHECKED_AT,
        },
      ],
      changements: [
        {
          id: "hotel-nantes-01",
          nom: "Hôtel des Machines",
          prix_avant: 96,
          prix_apres: 110,
          disponible_avant: true,
          disponible_apres: true,
          prix_change: true,
          disponibilite_change: false,
          inchange: false,
        },
      ],
    } as Proposition;

    render(<ProposalReview proposal={proposal} latestSearch={null} onChanged={() => {}} />);
    const newPrice = screen.getByText(/^110,00\s€$/);
    expect(newPrice).toHaveClass("text-brick", "font-semibold");
    expect(newPrice.closest("p")!).toHaveTextContent(/prix\s96,00\s€\s→/);
  });
});
