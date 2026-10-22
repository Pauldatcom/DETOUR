import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { renderLightMarkdown } from "./markdown";

function mount(source: string) {
  return render(<div data-testid="md">{renderLightMarkdown(source)}</div>);
}

describe("renderLightMarkdown", () => {
  it("renders plain text as a paragraph", () => {
    mount("Bonjour Détour");
    expect(screen.getByText("Bonjour Détour").tagName).toBe("P");
  });

  it("renders bold and italic", () => {
    mount("Le **prix** est *indicatif*.");
    expect(screen.getByText("prix").tagName).toBe("STRONG");
    expect(screen.getByText("indicatif").tagName).toBe("EM");
  });

  it("renders inline code", () => {
    mount("Utilisez `chercher_voyages`.");
    const code = screen.getByText("chercher_voyages");
    expect(code.tagName).toBe("CODE");
  });

  it("renders unordered and ordered lists", () => {
    mount("- Vol\n- Hôtel\n\n1. Réserver\n2. Confirmer");
    expect(screen.getByText("Vol").closest("ul")).toBeTruthy();
    expect(screen.getByText("Hôtel").closest("li")).toBeTruthy();
    expect(screen.getByText("Réserver").closest("ol")).toBeTruthy();
    expect(screen.getByText("Confirmer").closest("li")).toBeTruthy();
  });

  it("keeps soft line breaks inside a paragraph", () => {
    const { container } = mount("Ligne une\nLigne deux");
    expect(container.querySelectorAll("br")).toHaveLength(1);
    expect(container.textContent).toContain("Ligne une");
    expect(container.textContent).toContain("Ligne deux");
  });

  it("escapes HTML instead of executing it", () => {
    const { container } = mount('<script>alert("xss")</script> **ok**');
    expect(container.querySelector("script")).toBeNull();
    expect(container.textContent).toContain('<script>alert("xss")</script>');
    expect(screen.getByText("ok").tagName).toBe("STRONG");
  });

  it("only allows http(s) links", () => {
    mount("Voir [site](https://example.com) et [evil](javascript:alert(1)).");
    const link = screen.getByRole("link", { name: "site" });
    expect(link.getAttribute("href")).toBe("https://example.com");
    expect(link.getAttribute("rel")).toContain("noopener");
    // javascript: URL is not matched → left as plain text markers
    expect(screen.queryByRole("link", { name: "evil" })).toBeNull();
    expect(screen.getByTestId("md").textContent).toContain("[evil](javascript:alert(1))");
  });

  it("returns null for empty input", () => {
    const { container } = render(<div>{renderLightMarkdown("")}</div>);
    expect(container.textContent).toBe("");
  });
});
