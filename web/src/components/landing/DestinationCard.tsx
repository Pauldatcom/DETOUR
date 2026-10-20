import type { Destination } from "../../data/detourContent";

const GRADIENTS: Record<string, string> = {
  "dest-lisbonne": "linear-gradient(150deg, #f4b860, #e5716b, #7a5cd6)",
  "dest-kyoto": "linear-gradient(150deg, #b03a48, #5c1f30, #1d1024)",
  "dest-patagonie": "linear-gradient(150deg, #4a7ba6, #2b5577, #0b2447)",
  "dest-italie": "linear-gradient(150deg, #8db8d8, #38bdb8, #256d8a)",
  "dest-maroc": "linear-gradient(150deg, #f5b955, #d07a3e, #6b3226)",
  "dest-grece": "linear-gradient(150deg, #7fd9d5, #38bdb8, #1d7d8f)",
};

interface DestinationCardProps {
  destination: Destination;
  onDecouvrir: (d: Destination) => void;
}

/** Carte destination DÉTOUR — visuel dégradé fictif, prix indicatif « Exemple fictif ». */
export function DestinationCard({ destination, onDecouvrir }: DestinationCardProps) {
  return (
    <article className="group flex flex-col overflow-hidden rounded-2xl border border-[#e8eef6] bg-white shadow-sm transition hover:-translate-y-1 hover:shadow-lg">
      <div
        role="img"
        aria-label={destination.alt}
        className="relative aspect-[4/3] w-full"
        style={{ background: GRADIENTS[destination.id] ?? "linear-gradient(150deg, #8db8d8, #0b2447)" }}
      >
        <span className="absolute left-3 top-3 rounded-full bg-white/90 px-3 py-1 text-xs font-semibold text-[#0b2447]">
          {destination.region}
        </span>
        <span className="absolute bottom-3 right-3 rounded-full bg-black/40 px-3 py-1 text-xs font-medium text-white">
          Visuel fictif
        </span>
      </div>
      <div className="flex flex-1 flex-col p-5">
        <h3 className="text-lg font-bold text-[#0b2447]">{destination.titre}</h3>
        <p className="mt-1 text-xs font-semibold uppercase tracking-wide text-[#38bdb8]">
          {destination.ambiance}
        </p>
        <p className="mt-3 flex-1 text-sm leading-relaxed text-[#4b6480]">
          {destination.description}
        </p>
        <div className="mt-4 flex items-center justify-between">
          <span className="text-sm font-semibold text-[#0b2447]">{destination.prixIndicatif}</span>
          <button
            onClick={() => onDecouvrir(destination)}
            className="rounded-full bg-[#0b2447] px-4 py-2 text-sm font-semibold text-white outline-none transition hover:bg-[#12335e] focus-visible:ring-2 focus-visible:ring-[#38bdb8] focus-visible:ring-offset-2"
            aria-label={`Découvrir l'inspiration ${destination.titre}`}
          >
            Découvrir
          </button>
        </div>
      </div>
    </article>
  );
}
