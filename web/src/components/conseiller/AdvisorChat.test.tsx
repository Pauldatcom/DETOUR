import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AdvisorChat } from "./AdvisorChat";
import { api } from "../../lib/api";
import type { ConseillerChatResult, PrestationRecherche } from "../../types";

vi.mock("../../lib/api", () => ({
  api: {
    conseillerChat: vi.fn(),
    deciderProposition: vi.fn(),
    changerStatutProposition: vi.fn(),
    genererProposition: vi.fn(),
  },
}));

const conseillerChat = vi.mocked(api.conseillerChat);
const apiDecider = vi.mocked(api.deciderProposition);
const apiChangerStatut = vi.mocked(api.changerStatutProposition);
const apiGenerer = vi.mocked(api.genererProposition);
const AT = "2026-10-22T07:40:00+00:00";

function service(extra: Partial<PrestationRecherche>): PrestationRecherche {
  return {
    id: "x",
    nom: "x",
    type: "activite",
    destination: "Lyon",
    prix_unitaire_eur: 29,
    prix_total_eur: 58,
    disponible: true,
    dans_budget: true,
    places_restantes: 12,
    ...extra,
  };
}

function reply(
  resultats: PrestationRecherche[],
  statut = "ok",
  content = "Voici ce que j'ai vérifié.",
): ConseillerChatResult {
  return {
    reply: content,
    recherche: resultats.length
      ? { id: "r", source_label: "", source_url: "", consulte_le: AT, criteres: {}, resultats }
      : null,
    trace: { model: "m", tool_calls: [{ outil: "verifier_prestations", statut }] },
    simulation: true,
  };
}

const HOTEL = service({
  id: "hotel-lyon-01",
  nom: "Hôtel des Lumières",
  type: "hebergement",
  prix_unitaire_eur: 88,
  prix_total_eur: 176,
  places_restantes: 8,
});
const GAME = service({ id: "activite-lyon-01", nom: "Enquête des traboules" });
const FULL = service({
  id: "train-lyon-01",
  nom: "Train vers Lyon",
  type: "transport",
  disponible: false,
  places_restantes: 0,
});

async function openAndSend(text: string) {
  await userEvent.click(screen.getByRole("button", { name: "Ouvrir l'assistant" }));
  await userEvent.type(screen.getByLabelText("Message"), text);
  await userEvent.click(screen.getByRole("button", { name: "Envoyer" }));
}

describe("AdvisorChat", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("opens and closes, with an empty state that says nothing is booked", async () => {
    render(<AdvisorChat demandeId="dem_1" />);
    await userEvent.click(screen.getByRole("button", { name: "Ouvrir l'assistant" }));
    const dialog = screen.getByRole("dialog", { name: "Assistant conseiller" });
    expect(within(dialog).getByText("Dossier dem_1")).toBeInTheDocument();
    expect(within(dialog).getByText(/je ne réserve rien et je n'envoie rien/)).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Fermer l'assistant" }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("shows a checking state while the assistant works", async () => {
    let resolve: (value: ConseillerChatResult) => void = () => {};
    conseillerChat.mockReturnValue(new Promise((r) => (resolve = r)));
    render(<AdvisorChat demandeId="dem_1" />);
    await openAndSend("Vérifie Lyon");
    expect(screen.getByText("Je vérifie…")).toBeInTheDocument();
    expect(screen.getByText("Vérification en cours")).toBeInTheDocument();
    resolve(reply([HOTEL]));
    expect(await screen.findByText("Voici ce que j'ai vérifié.")).toBeInTheDocument();
    expect(screen.queryByText("Vérification en cours")).not.toBeInTheDocument();
  });

  it("sends the conversation with the request id and tells advisor and assistant apart", async () => {
    conseillerChat.mockResolvedValue(reply([HOTEL]));
    render(<AdvisorChat demandeId="dem_1" />);
    await openAndSend("Vérifie Lyon");
    await screen.findByText("Voici ce que j'ai vérifié.");
    expect(conseillerChat).toHaveBeenCalledWith(
      [{ role: "user", content: "Vérifie Lyon" }],
      "dem_1",
    );
    expect(screen.getByText("Vous")).toBeInTheDocument();
    expect(screen.getAllByText("Assistant").length).toBeGreaterThan(0);
  });

  it("shows structured option cards with verification states", async () => {
    conseillerChat.mockResolvedValue(reply([HOTEL, GAME, FULL]));
    render(<AdvisorChat />);
    await openAndSend("Lyon le 12 décembre pour 2");
    const options = await screen.findByRole("region", { name: "Options vérifiées" });
    const cards = within(options).getAllByRole("article");
    expect(cards).toHaveLength(3);
    expect(within(cards[0]).getByText(/^Vérifié · \d{1,2} h 40$/)).toBeInTheDocument();
    expect(within(cards[0]).getByText(/88\s€ par personne/)).toBeInTheDocument();
    expect(within(cards[0]).getByText(/Il reste 8 places/)).toBeInTheDocument();
    expect(within(cards[2]).getByText("Indisponible")).toBeInTheDocument();
    expect(within(cards[2]).getByText("Complet à cette date.")).toBeInTheDocument();
    expect(within(cards[2]).queryByText(/par personne/)).not.toBeInTheDocument();
    expect(screen.getByText(/Vérification terminée à .*Rien n'est réservé\./)).toBeInTheDocument();
  });

  it("flags a price that changed since an earlier reading", async () => {
    conseillerChat
      .mockResolvedValueOnce(reply([HOTEL]))
      .mockResolvedValueOnce(
        reply(
          [{ ...HOTEL, prix_unitaire_eur: 96, prix_total_eur: 192 }],
          "ok",
          "Nouvelle lecture.",
        ),
      );
    render(<AdvisorChat demandeId="dem_1" />);
    await openAndSend("Vérifie l'hôtel");
    await screen.findByText("Voici ce que j'ai vérifié.");
    await userEvent.type(screen.getByLabelText("Message"), "Revérifie");
    await userEvent.click(screen.getByRole("button", { name: "Envoyer" }));
    await screen.findByText("Nouvelle lecture.");
    expect(screen.getByText(/^Prix modifié · /)).toBeInTheDocument();
  });

  it("shows an error state when the assistant cannot answer", async () => {
    conseillerChat.mockRejectedValue(
      new Error(
        "L'assistant ne répond pas pour le moment. Le dossier reste consultable ; réessayez dans un instant.",
      ),
    );
    render(<AdvisorChat demandeId="dem_1" />);
    await openAndSend("Vérifie Lyon");
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "L'assistant ne répond pas pour le moment.",
    );
    expect(screen.getByText("Vérifie Lyon")).toBeInTheDocument();
  });

  it("shows an error state when the server check failed", async () => {
    conseillerChat.mockResolvedValue(reply([], "serveur_indisponible", "Je n'ai pas pu vérifier."));
    render(<AdvisorChat demandeId="dem_1" />);
    await openAndSend("Vérifie Lyon");
    await screen.findByText("Je n'ai pas pu vérifier.");
    expect(screen.getByText("Vérification impossible")).toBeInTheDocument();
    expect(screen.getByText(/aucun prix ni aucune place ne sont confirmés/)).toBeInTheDocument();
  });

  // -----------------------------------------------------------------------
  // Guardrails (#118): the advisor assistant cannot decide, send or animate
  // -----------------------------------------------------------------------
  describe("guardrails (#118)", () => {
    it("never calls a decision or generation endpoint after a chat exchange", async () => {
      conseillerChat.mockResolvedValue(reply([HOTEL]));
      render(<AdvisorChat demandeId="dem_1" />);
      await openAndSend("Vérifie Lyon");
      await screen.findByText("Voici ce que j'ai vérifié.");
      expect(apiDecider).not.toHaveBeenCalled();
      expect(apiChangerStatut).not.toHaveBeenCalled();
      expect(apiGenerer).not.toHaveBeenCalled();
    });

    it("never calls a decision or generation endpoint after an error", async () => {
      conseillerChat.mockRejectedValue(new Error("Serveur indisponible"));
      render(<AdvisorChat demandeId="dem_1" />);
      await openAndSend("Vérifie Lyon");
      await screen.findByRole("alert");
      expect(apiDecider).not.toHaveBeenCalled();
      expect(apiChangerStatut).not.toHaveBeenCalled();
      expect(apiGenerer).not.toHaveBeenCalled();
    });

    it("does not render the jumping-o animation (play class)", async () => {
      conseillerChat.mockResolvedValue(reply([HOTEL]));
      const { container } = render(<AdvisorChat demandeId="dem_1" />);
      await openAndSend("Vérifie Lyon");
      await screen.findByText("Voici ce que j'ai vérifié.");
      expect(container.querySelector(".play")).toBeNull();
    });
  });
});
