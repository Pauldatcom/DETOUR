import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { Login } from "./Login";
import { api } from "../lib/api";

vi.mock("../lib/api", () => ({
  api: { loginConseiller: vi.fn(), login: vi.fn(), register: vi.fn(), googleAuth: vi.fn() },
}));

function renderAdvisorTab() {
  render(
    <MemoryRouter>
      <Login onSession={() => {}} googleOauth={false} />
    </MemoryRouter>,
  );
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
