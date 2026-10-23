import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { Login } from "./Login";
import { api } from "../lib/api";

vi.mock("../lib/api", () => ({
  api: { loginConseiller: vi.fn(), login: vi.fn(), register: vi.fn(), googleAuth: vi.fn() },
}));

function renderLogin(props?: Partial<{ onSession: () => void; googleOauth: boolean }>) {
  return render(
    <MemoryRouter>
      <Login onSession={props?.onSession ?? (() => {})} googleOauth={props?.googleOauth ?? false} />
    </MemoryRouter>,
  );
}

function renderAdvisorTab() {
  renderLogin();
  return userEvent.click(screen.getByRole("tab", { name: "Conseiller" }));
}

describe("Login, advisor tab (#112)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("asks for the first name that signs the proposals", async () => {
    await renderAdvisorTab();
    expect(screen.getByLabelText("Votre prénom")).toBeInTheDocument();
    expect(
      screen.getByText("Les voyageurs le verront en signature de vos propositions."),
    ).toBeInTheDocument();
  });

  it("refuses to log in without a first name", async () => {
    await renderAdvisorTab();
    await userEvent.type(screen.getByLabelText("Clé d'accès conseiller"), "demo-key");
    await userEvent.click(screen.getByRole("button", { name: "Accéder" }));
    expect(screen.getByRole("alert")).toHaveTextContent("Indiquez votre prénom");
    expect(api.loginConseiller).not.toHaveBeenCalled();
  });

  it("sends the key and the first name", async () => {
    vi.mocked(api.loginConseiller).mockResolvedValue({
      session: { role: "conseiller", nom: "Camille" },
    });
    await renderAdvisorTab();
    await userEvent.type(screen.getByLabelText("Votre prénom"), " Camille ");
    await userEvent.type(screen.getByLabelText("Clé d'accès conseiller"), "demo-key");
    await userEvent.click(screen.getByRole("button", { name: "Accéder" }));
    expect(api.loginConseiller).toHaveBeenCalledWith("demo-key", "Camille");
  });
});

// -----------------------------------------------------------------------
// 2026 brand + accessibility (#126)
// -----------------------------------------------------------------------
describe("Login — 2026 brand & accessibility (#126)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("uses chalk background and ink text on the root", () => {
    const { container } = renderLogin();
    const root = container.firstElementChild as HTMLElement;
    expect(root.className).toContain("bg-chalk");
    expect(root.className).toContain("text-ink");
  });

  it("has a skip link to the form content", () => {
    renderLogin();
    const skip = screen.getByRole("link", { name: /aller au formulaire/i });
    expect(skip.getAttribute("href")).toBe("#contenu-connexion");
  });

  it("renders a tablist with an accessible label", () => {
    renderLogin();
    const tablist = screen.getByRole("tablist", { name: /mode de connexion/i });
    expect(tablist).toBeInTheDocument();
    expect(screen.getAllByRole("tab")).toHaveLength(3);
  });

  it("exposes all login fields with accessible labels", async () => {
    const user = userEvent.setup();
    renderLogin();
    expect(screen.getByLabelText(/e-mail/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/mot de passe/i)).toBeInTheDocument();
    await user.click(screen.getByRole("tab", { name: "Inscription" }));
    expect(screen.getByLabelText("Nom")).toBeInTheDocument();
  });

  it("exposes all advisor fields with accessible labels", async () => {
    await renderAdvisorTab();
    expect(screen.getByLabelText("Votre prénom")).toBeInTheDocument();
    expect(screen.getByLabelText("Clé d'accès conseiller")).toBeInTheDocument();
  });

  it("applies a visible focus ring class on every input", () => {
    renderLogin();
    const emailInput = screen.getByLabelText(/e-mail/i);
    expect(emailInput.className).toContain("focus:ring");
    expect(emailInput.className).toContain("focus:border-ink");
  });

  it("shows a role=status success banner after a successful login", async () => {
    const user = userEvent.setup();
    vi.mocked(api.login).mockResolvedValue({
      session: { role: "voyageur", nom: "Zoé" },
    });
    renderLogin();
    await user.type(screen.getByLabelText(/e-mail/i), "zoé@test.fr");
    await user.type(screen.getByLabelText(/mot de passe/i), "secret123");
    await user.click(screen.getByRole("button", { name: /se connecter/i }));
    await waitFor(() => {
      expect(screen.getByRole("status")).toBeInTheDocument();
    });
  });

  it("shows a role=alert error on a failed login", async () => {
    const user = userEvent.setup();
    vi.mocked(api.login).mockRejectedValue(new Error("Identifiants invalides"));
    renderLogin();
    await user.type(screen.getByLabelText(/e-mail/i), "zoé@test.fr");
    await user.type(screen.getByLabelText(/mot de passe/i), "wrongpass");
    await user.click(screen.getByRole("button", { name: /se connecter/i }));
    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
  });

  it("does not use any dark-mode variant (no dark: utilities)", () => {
    const { container } = renderLogin();
    expect(container.innerHTML).not.toContain("dark:");
  });
});
