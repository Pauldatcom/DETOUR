import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../../lib/api";
import type { ChatMessage } from "../../types";
import { AdvisorChatFrame } from "../conseiller/AdvisorChatFrame";
import { ChatBubble } from "../conseiller/ChatBubble";

interface ChatWidgetProps {
  isLoggedIn: boolean;
}

/**
 * Floating chat widget (bottom-left) — 2026 brand surface (#122).
 *
 * - Visible on public + traveler pages.
 * - Hidden on /login and /mes-propositions.
 * - No jumping-o in message copy; ≤1 yellow accent (monogram O).
 */
export function ChatWidget({ isLoggedIn }: ChatWidgetProps) {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  const pathname = window.location.pathname;
  const hidden = pathname === "/login" || pathname === "/mes-propositions";

  useEffect(() => {
    if (open && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [open, messages]);

  async function send(e: React.FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    if (!isLoggedIn) {
      navigate("/login");
      return;
    }

    const newMessages: ChatMessage[] = [...messages, { role: "user", content: text }];
    setMessages(newMessages);
    setInput("");
    setLoading(true);
    setError("");

    try {
      const result = await api.chat(newMessages);
      setMessages([...newMessages, { role: "assistant", content: result.reply || "…" }]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur");
      setMessages([
        ...newMessages,
        { role: "assistant", content: "Désolé, je n'ai pas pu répondre." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  if (hidden) return null;

  return (
    <AdvisorChatFrame
      title="PROPO · Assistant DÉTOUR"
      open={open}
      onClose={() => setOpen(false)}
      onToggle={() => setOpen((v) => !v)}
      scrollRef={scrollRef}
      input={input}
      onInputChange={setInput}
      onSubmit={send}
      loading={loading}
      inputPlaceholder={isLoggedIn ? "Votre message…" : "Connectez-vous pour discuter…"}
      submitDisabled={!input.trim()}
      error={error}
    >
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
      {loading && (
        <div className="flex justify-start">
          <ChatBubble role="assistant">…</ChatBubble>
        </div>
      )}
    </AdvisorChatFrame>
  );
}
