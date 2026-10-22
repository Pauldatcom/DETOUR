import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../../lib/api";
import type { ChatMessage } from "../../types";
import { AdvisorChatFrame } from "../conseiller/AdvisorChatFrame";
import { ChatBubble } from "../conseiller/ChatBubble";

const CONFIRMED_MESSAGE = "Merci, votre demande est transmise à un conseiller DÉTOUR.";
const DECLINED_MESSAGE = "D'accord, dites-moi ce que vous souhaitez modifier.";

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
  // Request saved by the agent in this conversation, and whether it waits for approval.
  const [requestId, setRequestId] = useState<string | undefined>();
  const [awaitingApproval, setAwaitingApproval] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const pathname = window.location.pathname;
  const hidden = pathname === "/login" || pathname === "/mes-propositions";

  useEffect(() => {
    if (open && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [open, messages]);

  // Restore a pending approval after a page reload: without this, the confirm
  // buttons vanish while the request stays "en_attente" and the advisor never sees it.
  useEffect(() => {
    if (!isLoggedIn || hidden) return;
    let cancelled = false;
    void (async () => {
      try {
        const { demandes } = await api.mesDemandes();
        if (cancelled) return;
        const pending = demandes.find((d) => d.approbation_client?.statut === "en_attente");
        if (pending) {
          setRequestId(pending.id);
          setAwaitingApproval(true);
        }
      } catch {
        // Silent: the approval is a best-effort restore, the chat stays usable.
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [isLoggedIn, hidden]);

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
      const result = await api.chat(newMessages, requestId);
      setMessages([...newMessages, { role: "assistant", content: result.reply || "…" }]);
      if (result.demande?.id) {
        setRequestId(result.demande.id);
        setAwaitingApproval(result.demande.approbation_client?.statut === "en_attente");
      }
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

  /** The traveler says yes or no: only then can the advisor get the request. */
  async function answer(confirmed: boolean) {
    if (!requestId) return;
    setError("");
    try {
      await api.approveRequest(requestId, confirmed);
      setAwaitingApproval(false);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: confirmed ? CONFIRMED_MESSAGE : DECLINED_MESSAGE },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur");
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
      {awaitingApproval && !loading && (
        <div className="flex flex-wrap justify-start gap-2">
          <button
            type="button"
            onClick={() => void answer(true)}
            className="rounded-full bg-ink px-4 py-2 text-sm font-semibold text-chalk"
          >
            Je confirme ma demande
          </button>
          <button
            type="button"
            onClick={() => void answer(false)}
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
    </AdvisorChatFrame>
  );
}
