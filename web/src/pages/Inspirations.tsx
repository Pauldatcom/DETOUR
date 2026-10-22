import { useState } from "react";
import { PublicNav } from "../components/landing/PublicNav";
import { Footer } from "../components/landing/Footer";
import { DestinationCard } from "../components/landing/DestinationCard";
import { ChatWidget } from "../components/landing/ChatWidget";
import { JumpingTitle } from "../lib/jumpingO";
import { INSPIRATIONS } from "../data/detourContent";
import type { Destination } from "../data/detourContent";
import type { Session } from "../types";

interface InspirationsPageProps {
  onDecrir: () => void;
  isLoggedIn: boolean;
  session: Session | null;
  onLogout: () => Promise<void>;
}

/** Page Inspirations — toutes les destinations, filtre par ambiance (2026 brand). */
export function InspirationsPage({
  onDecrir,
  isLoggedIn,
  session,
  onLogout,
}: InspirationsPageProps) {
  const ambiances = Array.from(new Set(INSPIRATIONS.destinations.map((d) => d.ambiance)));
  const [filtre, setFiltre] = useState<string | null>(null);

  const destinations = filtre
    ? INSPIRATIONS.destinations.filter((d) => d.ambiance === filtre)
    : INSPIRATIONS.destinations;

  return (
    <div className="min-h-screen bg-chalk text-ink">
      <PublicNav session={session} onLogout={onLogout} />
      <main className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:py-20">
        <div className="max-w-2xl">
          <p className="mb-2 font-mono text-xs font-semibold tracking-widest text-ballast uppercase">
            {INSPIRATIONS.surtitre}
          </p>
          <h1 className="text-3xl font-extrabold sm:text-4xl">
            <JumpingTitle text={INSPIRATIONS.titre} targetWord="inspirations" as="h1" />
          </h1>
          <p className="mt-4 text-ballast">{INSPIRATIONS.texte}</p>
        </div>

        <div className="mt-8 flex flex-wrap gap-2">
          <button
            onClick={() => setFiltre(null)}
            className={`rounded-full px-4 py-1.5 text-sm font-medium transition ${
              filtre === null
                ? "bg-ink text-chalk"
                : "border border-ink/20 text-ballast hover:bg-sky/40"
            }`}
          >
            Toutes
          </button>
          {ambiances.map((a) => (
            <button
              key={a}
              onClick={() => setFiltre(a)}
              className={`rounded-full px-4 py-1.5 text-sm font-medium transition ${
                filtre === a
                  ? "bg-ink text-chalk"
                  : "border border-ink/20 text-ballast hover:bg-sky/40"
              }`}
            >
              {a}
            </button>
          ))}
        </div>

        <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {destinations.map((d: Destination) => (
            <DestinationCard key={d.id} destination={d} onDecouvrir={() => onDecrir()} />
          ))}
        </div>
      </main>
      <Footer />
      <ChatWidget isLoggedIn={isLoggedIn} />
    </div>
  );
}
