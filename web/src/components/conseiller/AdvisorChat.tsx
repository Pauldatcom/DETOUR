import { useEffect, useRef, useState, type FormEvent } from "react";
import { api } from "../../lib/api";
import { formatClock } from "../../lib/tone";
import { etatPrestation, verificationEchouee } from "../../lib/verification";
import type { ChatMessage, PrestationRecherche, Recherche } from "../../types";
import { AdvisorChatFrame } from "./AdvisorChatFrame";
import { ChatBubble } from "./ChatBubble";
import { OptionCard } from "./OptionCard";
import { VerificationStateBadge } from "./VerificationStateBadge";

/** One turn shown in the chat. Assistant turns may carry a verified search. */
interface Turn {
  role: "advisor" | "assistant";
  content: string;
  search?: Recherche | null;
  failed?: boolean;
}

interface AdvisorChatProps {
  /** Request the advisor is working on; the assistant gets its context. */
  demandeId?: string | null;
}

const EMPTY_TEXT =
  "Posez une question sur ce dossier ou sur une destination. Je vérifie les prix et les places auprès du serveur ; je ne réserve rien et je n'envoie rien au voyageur.";

function toApiMessages(turns: Turn[]): ChatMessage[] {
  return turns.map((t) => ({
    role: t.role === "advisor" ? "user" : "assistant",
    content: t.content,
  }));
}

/** Latest reading of each service earlier in the conversation, to flag price changes. */
function previousReadings(turns: Turn[]): Map<string, PrestationRecherche> {
  const seen = new Map<string, PrestationRecherche>();
  for (const turn of turns) {
    for (const r of turn.search?.resultats ?? []) seen.set(r.id, r);
  }
  return seen;
}

/**
 * Advisor assistant chat (#120): open/close, send/receive, structured option
 * cards with verification states. The assistant suggests; the advisor decides.
 */
export function AdvisorChat({ demandeId = null }: AdvisorChatProps) {
  const [open, setOpen] = useState(false);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Instant jump, no smooth scroll: nothing moves on its own (reduced motion).
    if (open && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [open, turns, loading]);

  async function send(event: FormEvent) {
    event.preventDefault();
    const text = input.trim();
    if (!text || loading) return;
    const next: Turn[] = [...turns, { role: "advisor", content: text }];
    setTurns(next);
    setInput("");
    setLoading(true);
    setError("");
    try {
      const result = await api.conseillerChat(toApiMessages(next), demandeId);
      setTurns([
        ...next,
        {
          role: "assistant",
          content: result.reply || "Je n'ai pas de réponse à proposer pour l'instant.",
          search: result.recherche,
          failed: verificationEchouee(result.trace?.tool_calls),
        },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "L'assistant ne répond pas pour le moment.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AdvisorChatFrame
      title="Assistant conseiller"
      subtitle={demandeId ? `Dossier ${demandeId}` : "Aucun dossier ouvert"}
      open={open}
      onToggle={() => setOpen((value) => !value)}
      onClose={() => setOpen(false)}
      scrollRef={scrollRef}
      input={input}
      onInputChange={setInput}
      onSubmit={(e) => void send(e)}
      loading={loading}
      submitDisabled={!input.trim()}
      inputPlaceholder="Votre question à l'assistant…"
      error={error}
      launcherLabelOpen="Fermer l'assistant"
      launcherLabelClosed="Ouvrir l'assistant"
    >
      {turns.length === 0 && !loading && <ChatBubble role="system">{EMPTY_TEXT}</ChatBubble>}

      {turns.map((turn, index) =>
        turn.role === "advisor" ? (
          <ChatBubble key={index} role="advisor" label="Vous">
            {turn.content}
          </ChatBubble>
        ) : (
          <AssistantTurn key={index} turn={turn} earlier={turns.slice(0, index)} />
        ),
      )}

      {loading && (
        <div aria-live="polite" className="space-y-2">
          <ChatBubble role="assistant" label="Assistant">
            Je vérifie…
          </ChatBubble>
          <VerificationStateBadge state="checking" />
        </div>
      )}
    </AdvisorChatFrame>
  );
}

function AssistantTurn({ turn, earlier }: { turn: Turn; earlier: Turn[] }) {
  const results = turn.search?.resultats ?? [];
  const checkedAt = turn.search?.consulte_le ?? null;
  const previous = previousReadings(earlier);
  return (
    <div className="space-y-2">
      <ChatBubble role="assistant" label="Assistant">
        {turn.content}
      </ChatBubble>
      {turn.failed && (
        <div className="rounded-xl border border-brick/40 bg-white p-3 text-sm text-ink">
          <VerificationStateBadge state="error" />
          <p className="mt-1">
            La vérification n'a pas abouti : aucun prix ni aucune place ne sont confirmés.
          </p>
        </div>
      )}
      {results.length > 0 && (
        <section aria-label="Options vérifiées" className="space-y-2">
          {results.map((result) => {
            const before = previous.get(result.id);
            const state = etatPrestation(result, checkedAt, before);
            return (
              <OptionCard
                key={result.id}
                result={result}
                state={state}
                checkedAt={checkedAt}
                previousPrice={state === "modified" ? before?.prix_unitaire_eur : undefined}
              />
            );
          })}
          {checkedAt && (
            <p className="text-[11px] text-ballast">
              Vérification terminée à {formatClock(new Date(checkedAt))}. Rien n'est réservé.
            </p>
          )}
        </section>
      )}
    </div>
  );
}
