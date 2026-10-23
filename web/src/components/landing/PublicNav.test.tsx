import { describe, expect, it } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { PublicNav } from "./PublicNav";

/** The header exposes the dedicated chat window (#185) on desktop and mobile. */
function renderNav() {
  return render(
    <MemoryRouter initialEntries={["/accueil"]}>
      <PublicNav session={null} onLogout={async () => {}} />
    </MemoryRouter>,
  );
}

describe("PublicNav — Chat entry", () => {
  it("offers the chat window from the desktop header, right after Accueil", () => {
    const view = renderNav();
    const links = view.getAllByRole("link", { name: "Chat" });
    expect(links).toHaveLength(1);
    expect(links[0]).toHaveAttribute("href", "/chat");

    const order = within(document.querySelector("header nav")!)
      .getAllByRole("link")
      .map((l) => l.textContent)
      .filter((t) =>
        ["Accueil", "Chat", "Conseillers", "Comment ça marche", "Inspirations"].includes(t ?? ""),
      );
    expect(order).toEqual(["Accueil", "Chat", "Conseillers", "Comment ça marche", "Inspirations"]);
  });

  it("offers the chat window in the mobile menu, in the same order", async () => {
    const user = userEvent.setup();
    renderNav();
    await user.click(screen.getByRole("button", { name: /Ouvrir le menu/i }));
    expect(screen.getAllByRole("link", { name: "Chat" })).toHaveLength(2);
    const menu = document.getElementById("nav-mobile")!;
    const links = within(menu).getAllByRole("link", { name: "Chat" });
    expect(links).toHaveLength(1);
    expect(links[0]).toHaveAttribute("href", "/chat");
    const order = within(menu)
      .getAllByRole("listitem")
      .map((li) => li.textContent);
    expect(order.slice(0, 5)).toEqual([
      "Accueil",
      "Chat",
      "Conseillers",
      "Comment ça marche",
      "Inspirations",
    ]);
  });
});
