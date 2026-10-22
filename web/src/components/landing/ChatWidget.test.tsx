import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { ChatWidget } from "./ChatWidget";
import { api } from "../../lib/api";

// ---------------------------------------------------------------------------
// Module mocks (hoisted above imports by Vitest)
// ---------------------------------------------------------------------------

// Mock the navigate function so we can assert redirects without a real router.
const navigateMock = vi.fn();
vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal<typeof import("react-router-dom")>();
  return { ...actual, useNavigate: () => navigateMock };
});

// Mock the api module: only `chat` is used by ChatWidget.
vi.mock("../../lib/api", () => ({
  api: { chat: vi.fn() },
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Render the widget inside a MemoryRouter (required for useNavigate). */
function renderWidget(isLoggedIn = true) {
  return render(
    <MemoryRouter>
      <ChatWidget isLoggedIn={isLoggedIn} />
    </MemoryRouter>,
  );
}

/** Build a minimal ChatResult mock value. */
function makeResult(reply: string) {
  return {
    reply,
    demande: null,
    recherche: null,
    trace: { model: "test", tool_calls: [], simulation: true },
    simulation: true,
  } as ReturnType<typeof api.chat> extends Promise<infer T> ? T : never;
}

const apiChat = vi.mocked(api.chat);

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("ChatWidget", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset pathname to / before each test; ChatWidget reads window.location.pathname
    // directly at render time so each test starts from a known URL.
    window.history.pushState({}, "", "/");
  });

  // -------------------------------------------------------------------------
  // Visibility
  // -------------------------------------------------------------------------
  describe("visibility", () => {
    it("renders the bubble on a regular page", () => {
      renderWidget();
      expect(screen.getByRole("button", { name: /ouvrir le chat/i })).toBeInTheDocument();
    });

    it("returns null on /login", () => {
      window.history.pushState({}, "", "/login");
      const { container } = renderWidget();
      expect(container.firstChild).toBeNull();
    });

    it("returns null on /mes-propositions", () => {
      window.history.pushState({}, "", "/mes-propositions");
      const { container } = renderWidget();
      expect(container.firstChild).toBeNull();
    });
  });

  // -------------------------------------------------------------------------
  // Open / close
  // -------------------------------------------------------------------------
  describe("open / close", () => {
    it("opens the panel when the bubble is clicked", async () => {
      const user = userEvent.setup();
      renderWidget();
      const bubble = screen.getByRole("button", { name: /ouvrir le chat/i });
      expect(bubble).toHaveAttribute("aria-expanded", "false");
      await user.click(bubble);
      expect(screen.getByRole("dialog")).toBeInTheDocument();
      expect(bubble).toHaveAttribute("aria-expanded", "true");
    });

    it("closes the panel via the header close button", async () => {
      const user = userEvent.setup();
      renderWidget();
      await user.click(screen.getByRole("button", { name: /ouvrir le chat/i }));
      expect(screen.getByRole("dialog")).toBeInTheDocument();
      await user.click(screen.getByRole("button", { name: /^fermer$/i }));
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });

    it("toggles closed when the bubble is clicked again", async () => {
      const user = userEvent.setup();
      renderWidget();
      const bubble = screen.getByRole("button", { name: /ouvrir le chat/i });
      await user.click(bubble);
      expect(screen.getByRole("dialog")).toBeInTheDocument();
      await user.click(screen.getByRole("button", { name: /fermer le chat/i }));
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });
  });

  // -------------------------------------------------------------------------
  // Non-logged-in user
  // -------------------------------------------------------------------------
  describe("non-logged-in user", () => {
    it("shows a login prompt in the empty state", async () => {
      const user = userEvent.setup();
      renderWidget(false);
      await user.click(screen.getByRole("button", { name: /ouvrir le chat/i }));
      expect(screen.getByText(/connectez-vous/i)).toBeInTheDocument();
    });

    it("navigates to /login when a message is submitted", async () => {
      const user = userEvent.setup();
      renderWidget(false);
      await user.click(screen.getByRole("button", { name: /ouvrir le chat/i }));
      await user.type(screen.getByRole("textbox"), "Week-end à Lyon");
      await user.click(screen.getByRole("button", { name: /envoyer/i }));
      expect(navigateMock).toHaveBeenCalledWith("/login");
      expect(apiChat).not.toHaveBeenCalled();
    });
  });

  // -------------------------------------------------------------------------
  // Sending a message (advisor)
  // -------------------------------------------------------------------------
  describe("sending a message", () => {
    it("appends the user message and clears the input on submit", async () => {
      apiChat.mockResolvedValue(makeResult("Bonjour !"));
      const user = userEvent.setup();
      renderWidget();
      await user.click(screen.getByRole("button", { name: /ouvrir le chat/i }));
      const input = screen.getByRole("textbox");
      await user.type(input, "Bonjour le chat");
      await user.click(screen.getByRole("button", { name: /envoyer/i }));
      // User message visible
      expect(screen.getByText("Bonjour le chat")).toBeInTheDocument();
      // Input cleared
      expect(input).toHaveValue("");
    });

    it("does not send an empty message", async () => {
      const user = userEvent.setup();
      renderWidget();
      await user.click(screen.getByRole("button", { name: /ouvrir le chat/i }));
      await user.click(screen.getByRole("button", { name: /envoyer/i }));
      expect(apiChat).not.toHaveBeenCalled();
    });
  });

  // -------------------------------------------------------------------------
  // Chatbot response
  // -------------------------------------------------------------------------
  describe("receiving a chatbot response", () => {
    it("renders the assistant reply bubble", async () => {
      apiChat.mockResolvedValue(makeResult("Voici les prestations vérifiées pour Nantes."));
      const user = userEvent.setup();
      renderWidget();
      await user.click(screen.getByRole("button", { name: /ouvrir le chat/i }));
      await user.type(screen.getByRole("textbox"), "Week-end à Nantes");
      await user.click(screen.getByRole("button", { name: /envoyer/i }));
      expect(
        await screen.findByText("Voici les prestations vérifiées pour Nantes."),
      ).toBeInTheDocument();
    });

    it("falls back to '…' when reply is empty", async () => {
      apiChat.mockResolvedValue(makeResult(""));
      const user = userEvent.setup();
      renderWidget();
      await user.click(screen.getByRole("button", { name: /ouvrir le chat/i }));
      await user.type(screen.getByRole("textbox"), "test");
      await user.click(screen.getByRole("button", { name: /envoyer/i }));
      // The component uses `result.reply || "…"` → empty reply shows "…" as assistant bubble
      expect(await screen.findAllByText("…")).not.toHaveLength(0);
    });
  });

  // -------------------------------------------------------------------------
  // Loading state
  // -------------------------------------------------------------------------
  describe("loading state", () => {
    it("shows the ellipsis and disables input/button while the request is in flight", async () => {
      let resolveChat!: (v: ReturnType<typeof makeResult>) => void;
      apiChat.mockReturnValue(
        new Promise<ReturnType<typeof makeResult>>((r) => {
          resolveChat = r;
        }),
      );
      const user = userEvent.setup();
      renderWidget();
      await user.click(screen.getByRole("button", { name: /ouvrir le chat/i }));
      await user.type(screen.getByRole("textbox"), "Nantes");
      await user.click(screen.getByRole("button", { name: /envoyer/i }));

      // Loading indicators present
      expect(await screen.findByText("…")).toBeInTheDocument();
      expect(screen.getByRole("textbox")).toBeDisabled();
      expect(screen.getByRole("button", { name: /envoyer/i })).toBeDisabled();

      // Resolve and confirm loading state clears
      resolveChat(makeResult("Réponse reçue."));
      await waitFor(() => expect(screen.queryByRole("textbox")).not.toBeDisabled());
    });
  });

  // -------------------------------------------------------------------------
  // Backend error
  // -------------------------------------------------------------------------
  describe("backend error", () => {
    it("shows the alert with the error message and the sorry assistant bubble", async () => {
      apiChat.mockRejectedValue(new Error("Serveur indisponible"));
      const user = userEvent.setup();
      renderWidget();
      await user.click(screen.getByRole("button", { name: /ouvrir le chat/i }));
      await user.type(screen.getByRole("textbox"), "Lyon");
      await user.click(screen.getByRole("button", { name: /envoyer/i }));
      expect(await screen.findByRole("alert")).toHaveTextContent("Serveur indisponible");
      expect(screen.getByText(/désolé/i)).toBeInTheDocument();
    });
  });

  // -------------------------------------------------------------------------
  // Chatbot flow replies
  // Each flow is a distinct chatbot scenario. ChatWidget only renders result.reply,
  // so each test mocks api.chat to return the representative reply and asserts it
  // appears in the assistant bubble.
  // -------------------------------------------------------------------------
  describe("chatbot flow replies", () => {
    const flows: Array<{ name: string; reply: string }> = [
      {
        name: "unknown request",
        reply:
          "Je ne peux pas effectuer cette action. Seul l'outil de recherche de voyages est disponible.",
      },
      {
        name: "unverified price",
        reply:
          "Le prix de cette prestation n'a pas pu être vérifié auprès du serveur. Un conseiller confirmera les tarifs.",
      },
      {
        name: "unavailable activity",
        reply:
          "Cette prestation est indisponible pour les dates demandées. Voici les alternatives disponibles.",
      },
      {
        name: "alternative suggestion",
        reply:
          "L'activité principale est complète. Voici une alternative disponible qui correspond à votre séjour.",
      },
      {
        name: "draft proposal generation",
        reply:
          "Votre demande est bien enregistrée. Un conseiller préparera une proposition et vous la soumettra.",
      },
      {
        name: "advisor editing a draft",
        reply: "Le conseiller a mis à jour la proposition en tenant compte de vos retours.",
      },
      {
        name: "advisor confirmation",
        reply: "La proposition a été validée et vous sera envoyée par le conseiller.",
      },
      {
        name: "prevention of automatic chatbot confirmation",
        reply:
          "Je ne peux pas valider ou refuser une proposition : seul un conseiller humain prend cette décision.",
      },
      {
        name: "prevention of confirmation animation",
        reply:
          "La proposition reste à l'état brouillon. Aucune confirmation n'est déclenchée automatiquement.",
      },
    ];

    flows.forEach(({ name, reply }) => {
      it(`renders the assistant bubble for: ${name}`, async () => {
        apiChat.mockResolvedValue(makeResult(reply));
        const user = userEvent.setup();
        renderWidget();
        await user.click(screen.getByRole("button", { name: /ouvrir le chat/i }));
        await user.type(screen.getByRole("textbox"), "message");
        await user.click(screen.getByRole("button", { name: /envoyer/i }));
        expect(await screen.findByText(reply)).toBeInTheDocument();
      });
    });
  });

  // -------------------------------------------------------------------------
  // Responsive rendering (jsdom viewport)
  // -------------------------------------------------------------------------
  describe("responsive rendering", () => {
    it("renders a bubble visible at mobile viewport width", () => {
      Object.defineProperty(window, "innerWidth", {
        writable: true,
        configurable: true,
        value: 375,
      });
      renderWidget();
      expect(screen.getByRole("button", { name: /ouvrir le chat/i })).toBeInTheDocument();
    });

    it("constrains the panel width to the viewport", async () => {
      const user = userEvent.setup();
      renderWidget();
      await user.click(screen.getByRole("button", { name: /ouvrir le chat/i }));
      const panel = screen.getByRole("dialog");
      // The panel uses max-w-[calc(100vw-3rem)] to stay within any viewport.
      expect(panel.className).toContain("max-w-[calc(100vw-3rem)]");
    });
  });
});
