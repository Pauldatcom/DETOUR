import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { PropositionCard } from "./PropositionCard";
import type { Proposition } from "../types";

const CHECKED_AT = "2026-10-19T07:40:00+00:00";
const CHANGE_AT = "2026-10-20T09:00:00+00:00";

const PROPOSAL: Proposition = {
  id: "prop_1",
  demande_id: "dem_1",
  statut: "envoyee",
  cree_le: "2026-10-19T08:00:00+00:00",
  modifiee_le: "2026-10-19T08:00:00+00:00",
  conseiller: "Camille",
  titre: "Lyon en deux jours",
  description: "Un week-end à Lyon.",
  prix_total_eur: 358,
  prestations: [
    {
      id: "train-1",
      nom: "Train vers Lyon",
      type: "transport",
      quantite: 2,
      verification: "verifie",
      prix_unitaire_eur: 48,
      prix_total_eur: 96,
      disponible: true,
      source: "Serveur fictif DÉTOUR",
      consulte_le: CHECKED_AT,
    },
    {
      id: "hotel-1",
      nom: "Hôtel des Lumières",
      type: "hebergement",
      quantite: 2,
      verification: "verifie",
      prix_unitaire_eur: 96,
      prix_total_eur: 192,
      disponible: true,
      source: "Serveur fictif DÉTOUR",
      consulte_le: CHECKED_AT,
    },
    {
      id: "activity-1",
      nom: "Atelier",
      type: "activite",
      quantite: 2,
      verification: "manquant",
      prix_unitaire_eur: null,
      prix_total_eur: null,
      disponible: null,
      source: null,
      consulte_le: null,
    },
  ],
  changements: [
    {
      id: "train-1",
      nom: "Train vers Lyon",
      prix_avant: 48,
      prix_apres: 62,
      disponible_avant: true,
      disponible_apres: true,
      prix_change: true,
      disponibilite_change: false,
      inchange: false,
      consulte_le: CHANGE_AT,
    },
  ],
};

describe("PropositionCard", () => {
  it("renders verified, modified and missing states with dated amounts", () => {
    render(<PropositionCard proposition={PROPOSAL} linked={false} />);

    expect(screen.getByText("Lyon en deux jours")).toBeInTheDocument();
    expect(screen.getByText(/^62\s€ par personne\.$/)).toHaveClass("text-brick");
    expect(screen.getByText(/^Prix vérifié le 20\/10 à \d{1,2} h 00\.$/)).toBeInTheDocument();
    expect(screen.getByText(/Prix modifié\. Avant : 48\s€ par personne/)).toBeInTheDocument();
    expect(screen.getByText(/^96\s€ par personne\.$/)).toBeInTheDocument();
    expect(screen.getByText("Prix non vérifié.")).toBeInTheDocument();
    expect(screen.getByText(/^358\s€ au total\.$/)).toBeInTheDocument();
    expect(screen.getByText(/^Total des prestations vérifiées le 19\/10/)).toBeInTheDocument();
    expect(screen.getByText("Hors 1 prestation non vérifiée.")).toBeInTheDocument();
    expect(document.body.textContent).not.toMatch(/\*/);
  });
});
