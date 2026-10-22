import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { ChatBubble } from "./ChatBubble";

describe("ChatBubble markdown", () => {
  it("parses markdown for assistant string content", () => {
    render(<ChatBubble role="assistant">{"Le **prix** total"}</ChatBubble>);
    expect(screen.getByText("prix").tagName).toBe("STRONG");
  });

  it("leaves advisor (user) messages as plain text", () => {
    render(<ChatBubble role="advisor">{"Le **prix** total"}</ChatBubble>);
    expect(screen.queryByText("prix")).toBeNull();
    expect(screen.getByText("Le **prix** total")).toBeTruthy();
  });

  it("parses markdown for draft role", () => {
    render(<ChatBubble role="draft">{"- Option A\n- Option B"}</ChatBubble>);
    expect(screen.getByText("Option A").closest("ul")).toBeTruthy();
  });
});
