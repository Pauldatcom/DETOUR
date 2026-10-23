import type { ChatMessage } from "../../types";
import { ChatBubble } from "./ChatBubble";

interface ChatMessagesProps {
  messages: ChatMessage[];
  awaitingApproval: boolean;
  loading: boolean;
  isLoggedIn: boolean;
  onAnswer: (confirmed: boolean) => void;
}

/**
 * The conversation itself — bubbles, intro and approval buttons — shared by the
 * floating widget (#122) and the dedicated full-window chat page (#185).
 */
export function ChatConversation({
  messages,
  awaitingApproval,
  loading,
  isLoggedIn,
  onAnswer,
}: ChatMessagesProps) {
  return (
    <>
      {messages.length === 0 && !isLoggedIn && (
        <ChatBubble role="system">Connectez-vous pour discuter avec l'assistant.</ChatBubble>
      )}

      {messages.length === 0 && isLoggedIn && (
        <div className="flex justify-start">
          <ChatBubble role="assistant">
            <p>Bonjour, je suis PROPO.</p>
            <p className="mt-2">
              Dites-moi où, quand, à combien et votre budget par personne. Je vérifie les prix.
            </p>
          </ChatBubble>
        </div>
      )}

      {messages.map((m, i) => (
        <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
          <ChatBubble role={m.role === "user" ? "advisor" : "assistant"}>{m.content}</ChatBubble>
        </div>
      ))}
      {awaitingApproval && !loading && (
        <div className="flex flex-wrap justify-start gap-2">
          <button
            type="button"
            onClick={() => onAnswer(true)}
            className="rounded-full bg-ink px-4 py-2 text-sm font-semibold text-chalk"
          >
            Je confirme ma demande
          </button>
          <button
            type="button"
            onClick={() => onAnswer(false)}
            className="rounded-full border border-ink px-4 py-2 text-sm font-semibold text-ink"
          >
            Non, je veux modifier
          </button>
        </div>
      )}
      {loading && (
        <div className="flex justify-start">
          <ChatBubble role="assistant">…</ChatBubble>
        </div>
      )}
    </>
  );
}
