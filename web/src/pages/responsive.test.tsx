import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { Accueil } from "./Accueil";
import { Login } from "./Login";

vi.mock("../lib/api", () => ({
  api: {
    chat: vi.fn(),
    approveRequest: vi.fn(),
    mesDemandes: vi.fn().mockResolvedValue({ demandes: [] }),
    creerDemande: vi.fn(),
    login: vi.fn(),
    register: vi.fn(),
    loginConseiller: vi.fn(),
    googleAuth: vi.fn(),
    disponibilite: vi.fn().mockResolvedValue({ ouvert: true, message: "Ouvert" }),
  },
}));

const noop = async () => {};

function setViewport(width: number) {
  Object.defineProperty(window, "innerWidth", {
    writable: true,
    configurable: true,
    value: width,
  });
}

function renderScreen(element: React.ReactElement) {
  return render(<MemoryRouter>{element}</MemoryRouter>);
}

const VIEWPORTS: Array<{ name: string; width: number }> = [
  { name: "mobile (375px)", width: 375 },
  { name: "tablet (768px)", width: 768 },
  { name: "desktop (1280px)", width: 1280 },
];

describe("Responsive public screens (#126)", () => {
  describe("Accueil", () => {
    for (const { name, width } of VIEWPORTS) {
      it(`renders without crashing at ${name}`, () => {
        setViewport(width);
        const { container } = renderScreen(
          <Accueil isLoggedIn={false} session={null} onLogout={noop} />,
        );
        expect(container.firstElementChild).not.toBeNull();
        expect(screen.getByRole("button", { name: /ouvrir le chat/i })).toBeInTheDocument();
      });
    }
  });

  describe("Login", () => {
    for (const { name, width } of VIEWPORTS) {
      it(`renders the form at ${name}`, () => {
        setViewport(width);
        renderScreen(<Login onSession={() => {}} googleOauth={false} />);
        expect(screen.getByRole("tablist")).toBeInTheDocument();
        expect(screen.getByLabelText(/e-mail/i)).toBeInTheDocument();
      });
    }
  });
});
