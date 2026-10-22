import type { ReactNode } from "react";
import { renderLightMarkdown } from "../../lib/markdown";

/**
 * Message / content bubbles for the advisor chatbot surface.
 * Roles are visually distinct; no jumping-o typography in message text.
 * Assistant / draft / confirmed string bodies render a safe markdown subset (#154).
 */
export type ChatBubbleRole = "advisor" | "assistant" | "draft" | "confirmed" | "system";

interface ChatBubbleProps {
  role: ChatBubbleRole;
  children: ReactNode;
  label?: string;
}

const STYLES: Record<ChatBubbleRole, string> = {
  advisor: "ml-auto bg-ink text-chalk rounded-2xl rounded-br-md",
  assistant: "mr-auto bg-white text-ink border border-sky/60 rounded-2xl rounded-bl-md",
  draft: "mr-auto w-full bg-sky/35 text-ink border border-dashed border-ballast/50 rounded-2xl",
  confirmed: "mr-auto w-full bg-card text-ink border-2 border-ink rounded-2xl",
  system: "mx-auto max-w-[90%] bg-transparent text-ballast text-center text-sm",
};

const DEFAULT_LABEL: Partial<Record<ChatBubbleRole, string>> = {
  draft: "Brouillon généré par l'assistant",
  confirmed: "Confirmé par le conseiller",
};

const MARKDOWN_ROLES: ReadonlySet<ChatBubbleRole> = new Set(["assistant", "draft", "confirmed"]);

function Body({ role, children }: { role: ChatBubbleRole; children: ReactNode }) {
  if (MARKDOWN_ROLES.has(role) && typeof children === "string") {
    return <div className="font-sans">{renderLightMarkdown(children)}</div>;
  }
  return <div className="font-sans whitespace-pre-wrap">{children}</div>;
}

export function ChatBubble({ role, children, label }: ChatBubbleProps) {
  const badge = label ?? DEFAULT_LABEL[role];

  if (role === "system") {
    return <div className={`px-2 py-1 ${STYLES.system}`}>{children}</div>;
  }

  return (
    <div className={`max-w-[85%] px-3.5 py-2.5 text-sm leading-relaxed ${STYLES[role]}`}>
      {badge && (
        <p className="mb-1.5 font-display text-[11px] font-semibold tracking-wide text-ballast uppercase">
          {badge}
        </p>
      )}
      <Body role={role}>{children}</Body>
    </div>
  );
}
