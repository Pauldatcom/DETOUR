import { PublicNav } from "../components/landing/PublicNav";
import { BrandLogo } from "../components/conseiller/BrandLogo";
import { ChatConversation } from "../components/conseiller/ChatConversation";
import { useChat } from "../hooks/useChat";
import type { Session } from "../types";

interface ChatPageProps {
  isLoggedIn: boolean;
  session: Session | null;
  onLogout: () => Promise<void>;
}

/**
 * Dedicated full-window chat (#185) — reachable from the PublicNav "Chat"
 * entry and by deep link /chat. Same shared conversation as the floating
 * widget (#122), rendered as a focused surface: nav on top, live stream
 * filling the rest of the window, input anchored at the bottom, usable
 * down to mobile widths.
 */
export function ChatPage({ isLoggedIn, session, onLogout }: ChatPageProps) {
  const { messages, input, setInput, loading, error, awaitingApproval, scrollRef, submit, answer } =
    useChat({ isLoggedIn });

  return (
    <div className="flex h-screen flex-col bg-chalk text-ink">
      <PublicNav session={session} onLogout={onLogout} />
      <main
        id="contenu-principal"
        className="flex min-h-0 flex-1 flex-col overflow-hidden pt-6 sm:pt-10"
      >
        <div className="mx-auto flex min-h-0 w-full max-w-3xl flex-1 flex-col px-4 pb-6 sm:px-6 sm:pb-10">
          <header className="mb-5 flex items-center gap-4 rounded-2xl bg-ink px-5 py-4 text-chalk sm:mb-7 sm:px-6 sm:py-5">
            <BrandLogo width={44} variant="monogram" alt="" />
            <div className="min-w-0">
              <p className="font-display font-semibold tracking-tight text-base sm:text-lg">
                PROPO · Assistant DÉTOUR
              </p>
              <p className="mt-1 text-xs text-sky sm:text-sm">
                Un conseiller relit chaque demande, la vérifie et vous répond.
              </p>
            </div>
          </header>

          <div
            ref={scrollRef}
            className="min-h-0 flex-1 space-y-4 overflow-y-auto rounded-2xl border border-ink/10 bg-card px-5 py-5 sm:px-6"
          >
            <ChatConversation
              messages={messages}
              awaitingApproval={awaitingApproval}
              loading={loading}
              isLoggedIn={isLoggedIn}
              onAnswer={(confirmed) => void answer(confirmed)}
            />
            {error && (
              <p role="alert" className="text-xs text-brick">
                {error}
              </p>
            )}
          </div>

          <form
            onSubmit={submit}
            className="mt-4 flex items-center gap-2 rounded-2xl border border-ink/10 bg-chalk px-4 py-3 sm:mt-5"
          >
            <label htmlFor="chat-page-input" className="sr-only">
              Message
            </label>
            <input
              id="chat-page-input"
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={isLoggedIn ? "Votre message…" : "Connectez-vous pour discuter…"}
              className="min-w-0 flex-1 rounded-full border border-ink/15 bg-card px-4 py-2.5 text-sm text-ink transition outline-none placeholder:text-ballast focus:border-ink/40"
            />
            <button
              type="submit"
              disabled={!input.trim()}
              className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-ink text-chalk transition outline-none hover:bg-ink/90 disabled:opacity-40"
              aria-label="Envoyer"
            >
              <svg
                className="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={1.8}
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M6 12 3.75 3.75 20.25 12 3.75 20.25 6 12Zm0 0h7"
                />
              </svg>
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}
