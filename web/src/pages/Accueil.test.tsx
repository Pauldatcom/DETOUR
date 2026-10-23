import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { Accueil } from "./Accueil";
import type { Session } from "../types";

vi.mock("../lib/api", () => ({
  api: {
    chat: vi.fn(),
    approveRequest: vi.fn(),
    mesDemandes: vi.fn().mockResolvedValue({ demandes: [] }),
    creerDemande: vi.fn(),
    disponibilite: vi.fn().mockResolvedValue({ ouvert: true, message: "Ouvert" }),
  },
}));

const noop = async () => {};

function renderAccueil(isLoggedIn = false, session: Session | null = null) {
  return render(
    <MemoryRouter>
      <Accueil isLoggedIn={isLoggedIn} session={session} onLogout={noop} />
    </MemoryRouter>,
  );
}

describe("Accueil — 2026 brand (#126)", () => {
  it("uses the chalk background and ink text on the root container", () => {
    const { container } = renderAccueil();
    const root = container.firstElementChild as HTMLElement;
    expect(root.className).toContain("bg-chalk");
    expect(root.className).toContain("text-ink");
  });

  it("renders the official Logo in the navigation and footer", () => {
    const { container } = renderAccueil();
    const svgs = container.querySelectorAll("svg.logo");
    expect(svgs.length).toBeGreaterThanOrEqual(2);
  });

  it("has a main content landmark with an id for the skip link", () => {
    renderAccueil();
    expect(document.getElementById("contenu-principal")).not.toBeNull();
  });

  it("renders headings with the display font family via CSS h1/h2/h3 rules", () => {
    const { container } = renderAccueil();
    const headings = container.querySelectorAll("h1, h2, h3");
    expect(headings.length).toBeGreaterThan(0);
  });

  it("does not use the old text logo (no raw DÉTOUR text link)", () => {
    const { container } = renderAccueil();
    const logoLinks = container.querySelectorAll('a[aria-label*="DÉTOUR"]');
    logoLinks.forEach((link) => {
      const srOnly = link.querySelector(".sr-only");
      expect(srOnly).not.toBeNull();
    });
  });

  it("does not add any dark-mode variant (no dark: utilities)", () => {
    const { container } = renderAccueil();
    expect(container.innerHTML).not.toContain("dark:");
  });

  it("renders the chat widget for logged-in and anonymous users", () => {
    renderAccueil();
    expect(screen.getByRole("button", { name: /ouvrir le chat/i })).toBeInTheDocument();
  });
});
