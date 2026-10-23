import { useEffect, useRef, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import type { ChatMessage } from "../types";

const CONFIRMED_MESSAGE = "Merci, votre demande est transmise à un conseiller DÉTOUR.";
const DECLINED_MESSAGE = "D'accord, dites-moi ce que vous souhaitez modifier.";

export interface ChatConversationState {
  messages: ChatMessage[];
  input: string;
  setInput: (value: string) => void;
  loading: boolean;
  error: string;
  awaitingApproval: boolean;
  scrollRef: React.RefObject<HTMLDivElement | null>;
  submit: (e: FormEvent) => void;
  answer: (confirmed: boolean) => Promise<void>;
}

interface UseChatOptions {
  isLoggedIn: boolean;
  /**
   * When false, the pending-approval restore stays dormant (hidden pages).
   * `scrollKey` re-runs the scroll-to-latest effect: the widget passes its
   * open state so a reopened panel starts at the bottom, a full page omits it.
   */
  enabled?: boolean;
  scrollKey?: string | boolean | number;
}

/**
 * The PROPO conversation, shared by every chat surface (#185): the floating
 * widget (landing + account pages) and the dedicated full-window page /chat.
 *
 * - Sends `api.chat` with the whole thread and the request id when one exists.
 * - Restores the pending approval after a reload: pulls the traveler's
 *   en_attente request back into the conversation instead of losing buttons
 *   while the advisor waits.
 */
export function useChat({
  isLoggedIn,
  enabled = true,
  scrollKey,
}: UseChatOptions): ChatConversationState {
  const navigate = useNavigate();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  // Request saved by the agent in this conversation, and whether it waits for approval.
  const [requestId, setRequestId] = useState<string | undefined>();
  const [awaitingApproval, setAwaitingApproval] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, scrollKey]);

  // Restore a pending approval after a page reload: without this, the confirm
  // buttons vanish while the request stays "en_attente" and the advisor never sees it.
  useEffect(() => {
    if (!isLoggedIn || !enabled) return;
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
  }, [isLoggedIn, enabled]);

  function submit(e: FormEvent) {
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

    void (async () => {
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
    })();
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

  return {
    messages,
    input,
    setInput,
    loading,
    error,
    awaitingApproval,
    scrollRef,
    submit,
    answer,
  };
}
