import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../../lib/api";
import type { ChatMessage } from "../../types";

interface ChatWidgetProps {
  isLoggedIn: boolean;
}

/**
 * Floating chat widget (bottom-left).
 *
 * - Visible on public + traveler pages.
 * - Hidden on /login and /mes-propositions (advisor dashboard has its own tools).
 * - Non-logged-in users see a prompt to log in; no actual chat is sent.
 * - Logged-in users can chat; /api/chat already returns 401 without a session.
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
    <>
      {/* Bubble */}
      <button
        onClick={() => setOpen((v) => !v)}
        className="fixed bottom-6 left-6 z-40 flex h-14 w-14 items-center justify-center rounded-full bg-[#0b2447] text-white shadow-lg transition outline-none hover:bg-[#12335e] focus-visible:ring-2 focus-visible:ring-[#38bdb8] focus-visible:ring-offset-2"
        aria-label={open ? "Fermer le chat" : "Ouvrir le chat"}
        aria-expanded={open}
      >
        {open ? (
          <svg
            className="h-6 w-6"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1.5}
            aria-hidden="true"
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
          </svg>
        ) : (
          <svg
            className="h-6 w-6"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1.5}
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M7.5 8.25h9m-9 3.75h6m-6 5.25h9a4.5 4.5 0 0 0 4.5-4.5V6a4.5 4.5 0 0 0-4.5-4.5H6A4.5 4.5 0 0 0 1.5 6v6a4.5 4.5 0 0 0 4.5 4.5h1.5l3 3"
            />
          </svg>
        )}
      </button>

      {/* Panel */}
      {open && (
        <div
          className="fixed bottom-24 left-6 z-40 flex h-[420px] max-h-[80vh] w-[360px] max-w-[calc(100vw-3rem)] flex-col overflow-hidden rounded-2xl border border-[#e8eef6] bg-white shadow-2xl"
          role="dialog"
          aria-label="Chat DÉTOUR"
        >
          {/* Header */}
          <div className="flex items-center justify-between bg-[#0b2447] px-4 py-3 text-white">
            <div className="flex items-center gap-2">
              <span
                aria-hidden="true"
                className="grid h-7 w-7 place-items-center rounded-lg bg-white/10 text-sm font-bold"
              >
                D
              </span>
              <div>
                <p className="text-sm font-semibold">Assistant DÉTOUR</p>
                <p className="text-[10px] text-[#7fd9d5]">
                  Exemple fictif — conseiller sous 24-48 h
                </p>
              </div>
            </div>
            <button
              onClick={() => setOpen(false)}
              className="rounded-lg p-1 text-white/70 outline-none hover:bg-white/10 hover:text-white focus-visible:ring-2 focus-visible:ring-[#38bdb8]"
              aria-label="Fermer"
            >
              <svg
                className="h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
                aria-hidden="true"
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Messages */}
          <div ref={scrollRef} className="flex-1 overflow-y-auto bg-[#f7fafd] px-4 py-3">
            {messages.length === 0 && !isLoggedIn && (
              <div className="rounded-xl bg-[#f0eefe] px-4 py-3 text-sm text-[#6b3e9e]">
                Connectez-vous pour discuter avec l'assistant. Un conseiller vous répond sous 24 à
                48 h ouvrées.
              </div>
            )}
            {messages.length === 0 && isLoggedIn && (
              <div className="text-center text-sm text-[#8ba8c4]">
                Décrivez votre voyage, l'assistant vous aide à préparer votre demande.
              </div>
            )}
            {messages.map((m, i) => (
              <div
                key={i}
                className={`mb-3 flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-3.5 py-2 text-sm ${
                    m.role === "user"
                      ? "bg-[#0b2447] text-white"
                      : "border border-[#e8eef6] bg-white text-[#0b2447]"
                  }`}
                >
                  {m.content}
                </div>
              </div>
            ))}
            {loading && (
              <div className="mb-3 flex justify-start">
                <div className="rounded-2xl border border-[#e8eef6] bg-white px-3.5 py-2 text-sm text-[#8ba8c4]">
                  …
                </div>
              </div>
            )}
            {error && (
              <p role="alert" className="mt-2 text-xs text-[#b91c1c]">
                {error}
              </p>
            )}
          </div>

          {/* Input */}
          <form
            onSubmit={send}
            className="flex items-center gap-2 border-t border-[#e8eef6] bg-white px-3 py-2.5"
          >
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={isLoggedIn ? "Votre message…" : "Connectez-vous pour discuter…"}
              disabled={loading}
              className="flex-1 rounded-full bg-[#f7fafd] px-4 py-2 text-sm text-[#0b2447] outline-none placeholder:text-[#8ba8c4] focus:ring-2 focus:ring-[#38bdb8]/30"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="grid h-9 w-9 flex-shrink-0 place-items-center rounded-full bg-[#0b2447] text-white transition outline-none hover:bg-[#12335e] focus-visible:ring-2 focus-visible:ring-[#38bdb8] disabled:opacity-50"
              aria-label="Envoyer"
            >
              <svg
                className="h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={1.5}
                aria-hidden="true"
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 12 3 3l18 9-18 9 3-9Z" />
              </svg>
            </button>
          </form>
        </div>
      )}
    </>
  );
}
