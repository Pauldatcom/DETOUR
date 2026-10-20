import { useState } from "react";
import { PublicNav } from "../components/landing/PublicNav";
import { Footer } from "../components/landing/Footer";
import { DestinationCard } from "../components/landing/DestinationCard";
import { INSPIRATIONS } from "../data/detourContent";
import type { Destination } from "../data/detourContent";

interface InspirationsPageProps {
  onDecrir: () => void;
}

/** Page Inspirations — toutes les destinations, filtre par ambiance. */
export function InspirationsPage({ onDecrir }: InspirationsPageProps) {
  const ambiances = Array.from(
    new Set(INSPIRATIONS.destinations.map((d) => d.ambiance)),
  );
  const [filtre, setFiltre] = useState<string | null>(null);

  const destinations = filtre
    ? INSPIRATIONS.destinations.filter((d) => d.ambiance === filtre)
    : INSPIRATIONS.destinations;

  return (
    <div className="min-h-screen bg-white text-[#0b2447]">
      <PublicNav />
      <main className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:py-20">
        <div className="max-w-2xl">
          <p className="mb-2 text-sm font-semibold uppercase tracking-widest text-[#38bdb8]">
            {INSPIRATIONS.surtitre}
          </p>
          <h1 className="text-3xl font-bold sm:text-4xl">{INSPIRATIONS.titre}</h1>
          <p className="mt-4 text-[#4b6480]">{INSPIRATIONS.texte}</p>
        </div>

        <div className="mt-8 flex flex-wrap gap-2">
          <button
            onClick={() => setFiltre(null)}
            className={`rounded-full px-4 py-1.5 text-sm font-medium outline-none transition ${
              filtre === null
                ? "bg-[#0b2447] text-white"
                : "border border-[#d5e0ee] text-[#4b6480] hover:bg-[#f2f7fc]"
            }`}
          >
            Toutes
          </button>
          {ambiances.map((a) => (
            <button
              key={a}
              onClick={() => setFiltre(a)}
              className={`rounded-full px-4 py-1.5 text-sm font-medium outline-none transition ${
                filtre === a
                  ? "bg-[#0b2447] text-white"
                  : "border border-[#d5e0ee] text-[#4b6480] hover:bg-[#f2f7fc]"
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
    </div>
  );
}