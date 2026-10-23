import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { PriceVerification, ProposalTotal } from "./PriceVerification";
import type { ChangementLecture, Prestation, Proposition } from "../../types";

const CHECKED_AT = "2026-10-19T07:40:00+00:00";
const CHANGE_AT = "2026-10-20T09:00:00+00:00";

function service(extra: Partial<Prestation> = {}): Prestation {
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
    consulte_le: CHECKED_AT,
    ...extra,
  };
}

function change(extra: Partial<ChangementLecture> = {}): ChangementLecture {
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
    consulte_le: CHANGE_AT,
    ...extra,
  };
}

function proposition(prestations: Prestation[], extra: Partial<Proposition> = {}): Proposition {
  return {
    id: "prop_1",
    demande_id: "dem_1",
    statut: "envoyee",
    cree_le: "2026-10-19T08:00:00+00:00",
    modifiee_le: "2026-10-19T08:00:00+00:00",
    conseiller: "Camille",
    titre: "Lyon",
    description: "",
    prestations,
    prix_total_eur: prestations.reduce((total, line) => total + (line.prix_total_eur ?? 0), 0),
    ...extra,
  };
}

describe("PriceVerification", () => {
  it("shows a verified price with its date, availability and seats", () => {
    render(<PriceVerification service={service()} seats={6} showSource />);

    expect(screen.getByText(/^88\s€ par personne\.$/)).toBeInTheDocument();
    expect(screen.getByText(/^Prix vérifié le 19\/10 à \d{1,2} h 40\.$/)).toBeInTheDocument();
    expect(screen.getByText("Il reste 6 places à cette date.")).toBeInTheDocument();
    expect(
      screen.getByText(
        /^176\s€ au total pour ce poste, au prix vérifié le 19\/10 à \d{1,2} h 40\.$/,
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("Serveur fictif DÉTOUR")).toBeInTheDocument();
    expect(document.body.textContent).not.toMatch(/\*/);
  });

  it("shows checking without any amount or confirmed availability", () => {
    render(<PriceVerification service={service({ copie_depuis_v1: true })} />);

    expect(screen.getByText("Vérification en cours…")).toBeInTheDocument();
    expect(screen.getByText("Prix et disponibilité en cours de vérification.")).toBeInTheDocument();
    expect(
      screen.getByText("Prix repris de la proposition précédente, non relu."),
    ).toBeInTheDocument();
    expect(screen.queryByText(/88\s€/)).not.toBeInTheDocument();
    expect(document.body.textContent).not.toMatch(/\*/);
  });

  it("shows a modified price in Brick, with both prices dated", () => {
    render(<PriceVerification service={service()} change={change()} seats={2} />);

    const price = screen.getByText(/^96\s€ par personne\.$/);
    expect(price).toHaveClass("text-brick");
    expect(screen.getByText(/^Prix vérifié le 20\/10 à \d{1,2} h 00\.$/)).toBeInTheDocument();
    expect(screen.getByText(/Prix modifié\. Avant : 88\s€ par personne/)).toHaveTextContent(
      /vérifié le 19\/10 à \d{1,2} h 40/,
    );
    expect(screen.getByText("Il reste 2 places à cette date.")).toBeInTheDocument();
    expect(document.body.textContent).not.toMatch(/\*/);
  });

  it("says a place is complete without showing its price", () => {
    render(<PriceVerification service={service({ disponible: false })} />);

    expect(screen.getByText("Complet à cette date.")).toBeInTheDocument();
    expect(
      screen.getByText(/^Disponibilité vérifiée le 19\/10 à \d{1,2} h 40\.$/),
    ).toBeInTheDocument();
    expect(screen.queryByText(/88\s€/)).not.toBeInTheDocument();
    expect(document.body.textContent).not.toMatch(/\*/);
  });

  it("shows missing verification without inventing 0 € or confirming availability", () => {
    render(
      <PriceVerification
        service={service({
          verification: "manquant",
          prix_unitaire_eur: null,
          prix_total_eur: null,
          disponible: null,
          source: null,
          consulte_le: null,
        })}
      />,
    );

    expect(screen.getByText("Prix non vérifié.")).toBeInTheDocument();
    expect(screen.getByText("Disponibilité non vérifiée.")).toBeInTheDocument();
    expect(screen.queryByText(/0\s€/)).not.toBeInTheDocument();
    expect(document.body.textContent).not.toMatch(/\*/);
  });

  it("treats an undated price change as checking, not modified", () => {
    render(<PriceVerification service={service()} change={change({ consulte_le: null })} />);

    expect(screen.getByText("Vérification en cours…")).toBeInTheDocument();
    expect(screen.queryByText(/96\s€/)).not.toBeInTheDocument();
  });
});

describe("ProposalTotal", () => {
  it("dates the total from the latest verified line", () => {
    render(<ProposalTotal proposition={proposition([service()])} travelers={2} />);

    expect(screen.getByText(/^176\s€ pour 2 voyageurs\.$/)).toBeInTheDocument();
    expect(screen.getByText(/^Prix total vérifié le 19\/10 à \d{1,2} h 40\.$/)).toBeInTheDocument();
    expect(document.body.textContent).not.toMatch(/\*/);
  });

  it("names unverified lines outside a partial total", () => {
    const missing = service({
      id: "activity-1",
      nom: "Balade",
      verification: "manquant",
      prix_unitaire_eur: null,
      prix_total_eur: null,
      disponible: null,
      source: null,
      consulte_le: null,
    });
    render(<ProposalTotal proposition={proposition([service(), missing])} />);

    expect(screen.getByText(/^176\s€ au total\.$/)).toBeInTheDocument();
    expect(screen.getByText("Hors 1 prestation non vérifiée.")).toBeInTheDocument();
    expect(document.body.textContent).not.toMatch(/\*/);
  });

  it("shows no amount when no line is verified", () => {
    const missing = service({
      verification: "manquant",
      prix_unitaire_eur: null,
      prix_total_eur: null,
      disponible: null,
      source: null,
      consulte_le: null,
    });
    render(<ProposalTotal proposition={proposition([missing], { prix_total_eur: 0 })} />);

    expect(screen.getByText("Prix non vérifié.")).toBeInTheDocument();
    expect(screen.queryByText(/0\s€/)).not.toBeInTheDocument();
  });

  it("says when the total still includes a price copied from the previous version", () => {
    const copied = service({
      id: "hotel-copie",
      nom: "Hôtel repris",
      copie_depuis_v1: true,
      prix_unitaire_eur: 25,
      prix_total_eur: 50,
    });
    render(<ProposalTotal proposition={proposition([service(), copied])} />);

    expect(
      screen.getByText("Dont 1 prix repris de la proposition précédente."),
    ).toBeInTheDocument();
  });

  it("warns that the total predates a modified price", () => {
    render(
      <ProposalTotal
        proposition={proposition([service()], {
          changements: [change()],
        })}
      />,
    );

    expect(screen.getByText("Hors changements de prix signalés.")).toBeInTheDocument();
  });
});
