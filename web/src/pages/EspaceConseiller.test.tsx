import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { EspaceConseiller } from "./EspaceConseiller";
import { api } from "../lib/api";
import type { Demande, Proposition } from "../types";

vi.mock("../lib/api", () => ({
  api: {
    demandes: vi.fn(),
    demande: vi.fn(),
    propositions: vi.fn(),
    patchProposition: vi.fn(),
    deciderProposition: vi.fn(),
    decisionsPrestation: vi.fn(),
    rechercher: vi.fn(),
    genererProposition: vi.fn(),
    changerStatut: vi.fn(),
    changerQualification: vi.fn(),
  },
}));

const CHECKED_AT = "2026-10-22T07:40:00+00:00";

const REQUEST: Demande = {
  id: "dem_abc123",
  statut: "a_analyser",
  qualification: "pret_proposition",
  cree_le: "2026-10-21T08:00:00+00:00",
  echeance_cible: "2026-10-23T16:00:00+00:00",
  echeance_statut: "ok",
  champs_manquants: [],
  client: { id: "usr_1", nom: "Camille Martin", email: "camille@example.com" },
  demande: {
    type_voyage: "voyage-familial",
    destination: "Nantes",
    date_depart: "2026-11-07",
    date_retour: "2026-11-09",
    nombre_voyageurs: 3,
    has_enfants: true,
    nombre_enfants: 1,
    budget_max_par_personne: 250,
    niveau_aventure: "calme",
    besoin_guide: false,
    activites: ["créatif"],
    contraintes: "allergie aux arachides",
    conseiller: "",
    souhaits: "Un week-end tranquille",
    user_id: "usr_1",
  },
  recherches: [
    {
      id: "rech_1",
      source_label: "Serveur fictif DÉTOUR",
      source_url: "http://127.0.0.1:8765/api/v1/recherche",
      consulte_le: CHECKED_AT,
      criteres: {},
      resultats: [
        {
          id: "hotel-nantes-01",
          nom: "Hôtel des Machines",
          type: "hebergement",
          destination: "Nantes",
          prix_unitaire_eur: 96,
          prix_total_eur: 288,
          disponible: true,
          dans_budget: true,
          places_restantes: 6,
        },
      ],
    },
  ],
};

const DRAFT: Proposition = {
  id: "prop_1",
  demande_id: "dem_abc123",
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
    {
      id: "activite-inconnue",
      nom: "Atelier inventé",
      type: "activite",
      quantite: 3,
      verification: "manquant",
      prix_unitaire_eur: null,
      prix_total_eur: null,
      disponible: null,
      source: null,
      consulte_le: null,
    },
  ],
};

async function openRequest(proposal: Proposition = DRAFT) {
  vi.mocked(api.demandes).mockResolvedValue({ demandes: [REQUEST] });
  vi.mocked(api.demande).mockResolvedValue({ demande: REQUEST });
  vi.mocked(api.propositions).mockResolvedValue({ propositions: [proposal] });
  render(
    <MemoryRouter>
      <EspaceConseiller nom="Alice" onLogout={async () => {}} />
    </MemoryRouter>,
  );
  await userEvent.click(await screen.findByRole("button", { name: /Camille Martin/ }));
  return screen.findByRole("article");
}

describe("EspaceConseiller", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows the traveler and trip details in one place", async () => {
    await openRequest();
    const file = screen.getByRole("region", { name: "Dossier de la demande" });
    expect(within(file).getByText("camille@example.com")).toBeInTheDocument();
    expect(within(file).getByText("3 personnes, dont 1 enfant(s)")).toBeInTheDocument();
    expect(within(file).getByText("250 € par personne")).toBeInTheDocument();
    expect(within(file).getByText("allergie aux arachides")).toBeInTheDocument();
    expect(within(file).getByText("2 nuits")).toBeInTheDocument();
  });

  it("shows prices, seats, schedule and verification status of each service", async () => {
    const proposal = await openRequest();
    const rows = within(proposal).getAllByRole("row");
    const hotel = rows.find((r) => r.textContent?.includes("Hôtel des Machines"))!;
    expect(within(hotel).getByText("6")).toBeInTheDocument();
    expect(within(hotel).getByText("Non communiqué par le serveur")).toBeInTheDocument();
    expect(within(hotel).getByText(/^Vérifié le \d{2}\/\d{2} à \d{2}:\d{2}$/)).toBeInTheDocument();
    const invented = rows.find((r) => r.textContent?.includes("Atelier inventé"))!;
    expect(within(invented).getByText("Non vérifié")).toBeInTheDocument();
    expect(
      within(proposal).getByText(/1 prestation sans prix vérifié, hors total/),
    ).toBeInTheDocument();
  });

  it("makes the advisor's responsibility visible and never says the agent confirmed", async () => {
    await openRequest();
    expect(screen.getByText(/Vous êtes responsable de ce dossier/)).toBeInTheDocument();
    expect(screen.getByText("Brouillon préparé par l'assistant · non envoyé")).toBeInTheDocument();
    expect(document.body.textContent).not.toMatch(/confirm/i);
  });

  it("lets the advisor edit the title and message without touching the prices", async () => {
    vi.mocked(api.patchProposition).mockResolvedValue({ proposition: DRAFT });
    const proposal = await openRequest();
    await userEvent.click(
      within(proposal).getByRole("button", { name: "Modifier le titre et le message" }),
    );
    const title = within(proposal).getByLabelText("Titre");
    await userEvent.clear(title);
    await userEvent.type(title, "Nantes, à deux pas des Machines");
    await userEvent.click(
      within(proposal).getByRole("button", { name: "Enregistrer les modifications" }),
    );
    expect(api.patchProposition).toHaveBeenCalledWith("prop_1", {
      titre: "Nantes, à deux pas des Machines",
      description: "Deux jours au calme.",
      prestations: DRAFT.prestations,
    });
  });

  it("sends the proposal only after the advisor validates it", async () => {
    vi.mocked(api.deciderProposition).mockResolvedValue({ proposition: DRAFT });
    const proposal = await openRequest();
    await userEvent.click(
      within(proposal).getByRole("button", { name: "Valider et envoyer au voyageur" }),
    );
    expect(api.deciderProposition).not.toHaveBeenCalled();
    expect(
      within(proposal).getByText("Vous envoyez cette proposition au voyageur, en votre nom."),
    ).toBeInTheDocument();
    await userEvent.click(within(proposal).getByRole("button", { name: "Envoyer au voyageur" }));
    expect(api.deciderProposition).toHaveBeenCalledWith("prop_1", "accepter", "", undefined);
  });

  it("requires a reason before refusing a proposal", async () => {
    const proposal = await openRequest();
    await userEvent.click(within(proposal).getByRole("button", { name: "Refuser" }));
    await userEvent.click(within(proposal).getByRole("button", { name: "Enregistrer" }));
    expect(within(proposal).getByRole("alert")).toHaveTextContent(
      "Indiquez le motif de votre décision.",
    );
    expect(api.deciderProposition).not.toHaveBeenCalled();
  });

  it("hides editing and decisions once the proposal is sent", async () => {
    const proposal = await openRequest({ ...DRAFT, statut: "envoyee" });
    expect(
      within(proposal).getByText("Envoyée au voyageur · en attente de sa réponse"),
    ).toBeInTheDocument();
    expect(
      within(proposal).queryByRole("button", { name: "Modifier le titre et le message" }),
    ).not.toBeInTheDocument();
    expect(
      within(proposal).queryByRole("button", { name: "Valider et envoyer au voyageur" }),
    ).not.toBeInTheDocument();
  });

  // #121: the jumping-o animation fires only on the advisor's explicit
  // confirmation — never from chatbot output or any other action.
  it("plays the jumping-o animation only after the advisor confirms", async () => {
    vi.mocked(api.deciderProposition).mockResolvedValue({ proposition: DRAFT });
    const proposal = await openRequest();
    expect(proposal.querySelector(".play")).toBeNull();
    await userEvent.click(
      within(proposal).getByRole("button", { name: "Valider et envoyer au voyageur" }),
    );
    await userEvent.click(within(proposal).getByRole("button", { name: "Envoyer au voyageur" }));
    const banner = await screen.findByRole("article");
    expect(banner.querySelector(".play")).not.toBeNull();
  });

  it("lets the advisor sign the draft with their first name", async () => {
    vi.mocked(api.patchProposition).mockResolvedValue({ proposition: DRAFT });
    const proposal = await openRequest();
    await userEvent.click(
      within(proposal).getByRole("button", { name: "Modifier le titre et le message" }),
    );
    const name = within(proposal).getByLabelText("Votre prénom (signe la proposition)");
    await userEvent.clear(name);
    await userEvent.type(name, "Camille");
    await userEvent.click(
      within(proposal).getByRole("button", { name: "Enregistrer les modifications" }),
    );
    expect(api.patchProposition).toHaveBeenCalledWith(
      "prop_1",
      expect.objectContaining({ conseiller: "Camille" }),
    );
  });

  it("lets the advisor drop a prestation from the draft", async () => {
    vi.mocked(api.patchProposition).mockResolvedValue({ proposition: DRAFT });
    const proposal = await openRequest();
    await userEvent.click(
      within(proposal).getByRole("button", { name: "Modifier le titre et le message" }),
    );
    const checkbox = within(proposal).getByRole("checkbox", {
      name: /Atelier inventé/,
    });
    await userEvent.click(checkbox);
    await userEvent.click(
      within(proposal).getByRole("button", { name: "Enregistrer les modifications" }),
    );
    expect(api.patchProposition).toHaveBeenCalledWith(
      "prop_1",
      expect.objectContaining({
        prestations: [DRAFT.prestations[0]],
      }),
    );
  });
});
