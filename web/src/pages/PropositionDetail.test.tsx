import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { PropositionDetail } from "./PropositionDetail";
import { api } from "../lib/api";
import type { Demande, Proposition } from "../types";

vi.mock("../lib/api", () => ({
  api: { proposition: vi.fn(), demande: vi.fn() },
}));

const CHECKED_AT = "2026-10-19T07:40:00+00:00";

const PROPOSAL: Proposition = {
  id: "prop_1",
  demande_id: "dem_1",
  statut: "envoyee",
  cree_le: "2026-10-19T08:00:00+00:00",
  modifiee_le: "2026-10-19T08:00:00+00:00",
  conseiller: "Conseiller DÉTOUR",
  titre: "Nantes en deux jours",
  description:
    "L'atelier du samedi est complet.\nJe vous propose dimanche à 10 h, pour le même prix.",
  prix_total_eur: 358,
  decisions_statut: [{ action: "accepter", par: "Camille", le: "2026-10-19T08:10:00+00:00" }],
  prestations: [
    {
      id: "train-nantes-01",
      nom: "Train vers Nantes",
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
      id: "hotel-nantes-01",
      nom: "Hôtel des Machines",
      type: "hebergement",
      quantite: 4,
      verification: "verifie",
      prix_unitaire_eur: 96,
      prix_total_eur: 384,
      disponible: true,
      source: "Serveur fictif DÉTOUR",
      consulte_le: CHECKED_AT,
    },
    {
      id: "activite-nantes-01",
      nom: "Atelier de machines imaginaires",
      type: "activite",
      quantite: 2,
      verification: "verifie",
      prix_unitaire_eur: 35,
      prix_total_eur: 70,
      disponible: false,
      source: "Serveur fictif DÉTOUR",
      consulte_le: CHECKED_AT,
    },
    {
      id: "activite-inconnue",
      nom: "Balade en barque",
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
};

const REQUEST = {
  id: "dem_1",
  statut: "propose",
  cree_le: "",
  demande: {
    destination: "Nantes",
    date_depart: "2026-11-07",
    date_retour: "2026-11-09",
    nombre_voyageurs: 2,
  },
  recherches: [
    {
      id: "rech_1",
      source_label: "Serveur fictif DÉTOUR",
      source_url: "",
      consulte_le: CHECKED_AT,
      criteres: {},
      resultats: [
        {
          id: "hotel-nantes-01",
          nom: "Hôtel des Machines",
          type: "hebergement",
          destination: "Nantes",
          prix_unitaire_eur: 96,
          prix_total_eur: 192,
          disponible: true,
          dans_budget: true,
          places_restantes: 6,
        },
      ],
    },
  ],
} as unknown as Demande;

function renderPage() {
  return render(
    <MemoryRouter initialEntries={["/mon-compte/propositions/prop_1"]}>
      <Routes>
        <Route path="/mon-compte/propositions/:id" element={<PropositionDetail />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("PropositionDetail", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.proposition).mockResolvedValue({ proposition: PROPOSAL });
    vi.mocked(api.demande).mockResolvedValue({ demande: REQUEST });
  });

  it("shows the full itinerary", async () => {
    renderPage();
    expect(await screen.findByText("Nantes en deux jours")).toBeInTheDocument();
    expect(
      screen.getByText("Du samedi 7 novembre au lundi 9 novembre · 2 nuits · 2 voyageurs"),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Le trajet" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Où vous dormez" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Ce que vous faites" })).toBeInTheDocument();
  });

  it("shows each price per person with its check date, and the seats left", async () => {
    renderPage();
    await screen.findByText("Nantes en deux jours");
    expect(screen.getAllByText(/^96\s€ par personne\.$/)).toHaveLength(1);
    expect(screen.getAllByText(/^Prix vérifié le 19\/10 à \d{1,2} h 40\.$/)).toHaveLength(2);
    expect(screen.getByText("Il reste 6 places à cette date.")).toBeInTheDocument();
  });

  it("says plainly when a service is fully booked or not yet checked", async () => {
    renderPage();
    await screen.findByText("Nantes en deux jours");
    expect(screen.getByText("Complet à cette date.")).toBeInTheDocument();
    expect(screen.getByText("Prix non vérifié.")).toBeInTheDocument();
    expect(screen.getByText("Disponibilité non vérifiée.")).toBeInTheDocument();
    expect(screen.getByText("Hors 1 prestation non vérifiée.")).toBeInTheDocument();
  });

  it("signs the message with the advisor's first name", async () => {
    renderPage();
    await screen.findByText("Nantes en deux jours");
    const message = screen.getByRole("region", { name: "Message de votre conseiller" });
    expect(message).toHaveTextContent("Je vous propose dimanche à 10 h, pour le même prix.");
    expect(message).toHaveTextContent(/Camille$/);
  });

  it("says nothing is booked and shows no technical ids or exaggerated claims", async () => {
    renderPage();
    await screen.findByText("Nantes en deux jours");
    expect(
      screen.getByText("Rien n'est réservé pour l'instant : votre conseiller attend votre retour."),
    ).toBeInTheDocument();
    const text = document.body.textContent ?? "";
    expect(text).not.toMatch(/hotel-nantes-01|train-nantes-01|activite-/);
    expect(text).not.toMatch(/!|inoubliable|de rêve|confirm/i);
  });

  it("still shows the proposal when the request cannot be read", async () => {
    vi.mocked(api.demande).mockRejectedValue(new Error("Demande introuvable."));
    renderPage();
    expect(await screen.findByText("Nantes en deux jours")).toBeInTheDocument();
    expect(screen.getByText(/^358\s€ au total\.$/)).toBeInTheDocument();
  });
});
