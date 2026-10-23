import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ChatPage } from "./ChatPage";
import { api } from "../lib/api";
import type { Demande } from "../types";

vi.mock("../lib/api", () => ({
  api: { chat: vi.fn(), approveRequest: vi.fn(), mesDemandes: vi.fn() },
}));

const apiChat = vi.mocked(api.chat);
const apiApprove = vi.mocked(api.approveRequest);
const apiMesDemandes = vi.mocked(api.mesDemandes);

/*
 * Dedicated chat window (#185): /chat renders the shared PROPO conversation
 * in its own window, reachable by deep link; the conversation works end to
 * end (message -> agent reply -> approval flow), and an anonymous visitor is
 * sent to /login when trying to send.
 */

function chatResult(reply: string) {
  return {
    reply,
    demande: null,
    recherche: null,
    trace: { model: "test", tool_calls: [], simulation: true },
    simulation: true,
  } as Awaited<ReturnType<typeof api.chat>>;
}

const PENDING_DEMANDES: { demandes: Demande[] } = {
  demandes: [
    {
      id: "dem_abc123",
      statut: "nouvelle",
      cree_le: "2026-10-23T10:00:00+00:00",
      approbation_client: { statut: "en_attente", le: null },
    },
  ] as unknown as Demande[],
};

function renderChat(page = "/chat", isLoggedIn = false) {
  return render(
    <MemoryRouter initialEntries={[page]}>
      <Routes>
        <Route
          path="/chat"
          element={<ChatPage isLoggedIn={isLoggedIn} session={null} onLogout={async () => {}} />}
        />
        <Route path="/login" element={<p>PAGE-LOGIN</p>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("ChatPage — dedicated window", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiMesDemandes.mockResolvedValue({ demandes: [] } as Awaited<
      ReturnType<typeof api.mesDemandes>
    >);
  });

  it("renders by deep link with the PROPO header and the intro bubble", async () => {
    renderChat("/chat", true);
    expect(screen.getByText("PROPO · Assistant DÉTOUR")).toBeInTheDocument();
    expect(await screen.findByText(/Bonjour, je suis PROPO/i)).toBeInTheDocument();
  });

  it("sends a message end to end and shows the agent reply", async () => {
    const user = userEvent.setup();
    apiChat.mockResolvedValue(chatResult("Votre demande est prête."));
    renderChat("/chat", true);

    await user.type(screen.getByLabelText("Message"), "Train pour Nantes");
    await user.click(screen.getByRole("button", { name: /envoyer/i }));

    await waitFor(() => {
      expect(apiChat).toHaveBeenCalledWith(
        [expect.objectContaining({ role: "user", content: "Train pour Nantes" })],
        undefined,
      );
    });
    expect(await screen.findByText("Votre demande est prête.")).toBeInTheDocument();
    expect(screen.getByText("Train pour Nantes")).toBeInTheDocument();
  });

  it("sends an anonymous visitor to /login instead of calling the agent", async () => {
    const user = userEvent.setup();
    renderChat("/chat", false);

    await user.type(screen.getByLabelText("Message"), "Bonjour");
    await user.click(screen.getByRole("button", { name: /envoyer/i }));

    await waitFor(() => expect(screen.getByText("PAGE-LOGIN")).toBeInTheDocument());
    expect(apiChat).not.toHaveBeenCalled();
  });

  it("restores a pending approval and confirms it end to end", async () => {
    const user = userEvent.setup();
    apiMesDemandes.mockResolvedValue(
      PENDING_DEMANDES as Awaited<ReturnType<typeof api.mesDemandes>>,
    );
    apiApprove.mockResolvedValue({} as Awaited<ReturnType<typeof api.approveRequest>>);
    renderChat("/chat", true);

    const confirm = await screen.findByRole("button", { name: /Je confirme ma demande/i });
    await user.click(confirm);

    await waitFor(() => expect(apiApprove).toHaveBeenCalledWith("dem_abc123", true));
    expect(
      await screen.findByText("Merci, votre demande est transmise à un conseiller DÉTOUR."),
    ).toBeInTheDocument();
  });
});
