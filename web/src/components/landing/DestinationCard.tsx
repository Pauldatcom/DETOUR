import type { Destination } from "../../data/detourContent";

/* Fictive destination visuals — 2026 brand palette only (sky, ink, yellow, brick). */
const GRADIENTS: Record<string, string> = {
  "dest-lisbonne": "linear-gradient(150deg, #f2b705, #c4553a, #16233f)",
  "dest-kyoto": "linear-gradient(150deg, #c4553a, #6b2f3c, #16233f)",
  "dest-patagonie": "linear-gradient(150deg, #bcd3ea, #4c7cab, #16233f)",
  "dest-italie": "linear-gradient(150deg, #bcd3ea, #8fb4d6, #16233f)",
  "dest-maroc": "linear-gradient(150deg, #f2b705, #c07a3e, #16233f)",
  "dest-grece": "linear-gradient(150deg, #bcd3ea, #7ea8cf, #16233f)",
};

interface DestinationCardProps {
  destination: Destination;
  onDecouvrir: (d: Destination) => void;
}

/** Carte destination DÉTOUR — visuel dégradé fictif, prix indicatif « Exemple fictif ». */
export function DestinationCard({ destination, onDecouvrir }: DestinationCardProps) {
  return (
    <article className="group flex flex-col overflow-hidden rounded-2xl border border-line bg-card shadow-sm transition hover:-translate-y-1 hover:shadow-lg">
      <div
        role="img"
        aria-label={destination.alt}
        className="relative aspect-[4/3] w-full"
        style={{
          background: GRADIENTS[destination.id] ?? "linear-gradient(150deg, #bcd3ea, #16233f)",
        }}
      >
        <span className="absolute top-3 left-3 rounded-full bg-chalk/90 px-3 py-1 text-xs font-semibold text-ink">
          {destination.region}
        </span>
        <span className="absolute right-3 bottom-3 rounded-full bg-ink/50 px-3 py-1 font-mono text-xs text-chalk">
          Visuel fictif
        </span>
      </div>
      <div className="flex flex-1 flex-col p-5">
        <h3 className="text-lg font-extrabold text-ink">{destination.titre}</h3>
        <p className="mt-1 font-mono text-xs font-semibold tracking-wide text-ballast uppercase">
          {destination.ambiance}
        </p>
        <p className="mt-3 flex-1 text-sm leading-relaxed text-ballast">
          {destination.description}
        </p>
        <div className="mt-4 flex items-center justify-between">
          <span className="text-sm font-semibold text-ink">{destination.prixIndicatif}</span>
          <button
            onClick={() => onDecouvrir(destination)}
            className="rounded-full bg-ink px-4 py-2 text-sm font-semibold text-chalk transition hover:bg-ink/85"
            aria-label={`Découvrir l'inspiration ${destination.titre}`}
          >
            Découvrir
          </button>
        </div>
      </div>
    </article>
  );
}
