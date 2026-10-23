import { useState } from "react";
import { AdvisorChatFrame } from "../conseiller/AdvisorChatFrame";
import { ChatConversation } from "../conseiller/ChatConversation";
import { useChat } from "../../hooks/useChat";

interface ChatWidgetProps {
  isLoggedIn: boolean;
}

/**
 * Floating chat widget (bottom-left) — 2026 brand surface (#122).
 *
 * - Visible on public + traveler pages; hidden on /login, /mes-propositions
 *   and /chat (the dedicated window #185 replaces it there).
 * - The conversation logic (states, api, pending approval) lives in
 *   useChat + ChatConversation, shared with the /chat page — no duplicated
 *   business logic between the two surfaces.
 * - No jumping-o in message copy; ≤1 yellow accent (monogram O).
 */
export function ChatWidget({ isLoggedIn }: ChatWidgetProps) {
  const [open, setOpen] = useState(false);

  const pathname = window.location.pathname;
  const hidden = pathname === "/login" || pathname === "/mes-propositions" || pathname === "/chat";

  const chat = useChat({ isLoggedIn, enabled: !hidden, scrollKey: open ? "open" : "closed" });

  if (hidden) return null;

  return (
    <AdvisorChatFrame
      title="PROPO · Assistant DÉTOUR"
      open={open}
      onClose={() => setOpen(false)}
      onToggle={() => setOpen((v) => !v)}
      scrollRef={chat.scrollRef}
      input={chat.input}
      onInputChange={chat.setInput}
      onSubmit={chat.submit}
      loading={chat.loading}
      inputPlaceholder={isLoggedIn ? "Votre message…" : "Connectez-vous pour discuter…"}
      submitDisabled={!chat.input.trim()}
      error={chat.error}
    >
      <ChatConversation
        messages={chat.messages}
        awaitingApproval={chat.awaitingApproval}
        loading={chat.loading}
        isLoggedIn={isLoggedIn}
        onAnswer={(confirmed) => void chat.answer(confirmed)}
      />
    </AdvisorChatFrame>
  );
}
