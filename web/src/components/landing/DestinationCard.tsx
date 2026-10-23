import type { Destination } from "../../data/detourContent";

interface DestinationCardProps {
  destination: Destination;
  onDecouvrir: (d: Destination) => void;
}

/** Carte destination DÉTOUR — photo brand-2026, prix indicatif « Exemple fictif ». */
export function DestinationCard({ destination, onDecouvrir }: DestinationCardProps) {
  return (
    <article className="group flex flex-col overflow-hidden rounded-2xl border border-line bg-card shadow-sm transition hover:-translate-y-1 hover:shadow-lg">
      <div className="relative aspect-[4/3] w-full overflow-hidden">
        <img
          src={destination.image}
          alt={destination.alt}
          loading="lazy"
          className="h-full w-full object-cover"
        />
        <span className="absolute top-3 left-3 rounded-full bg-chalk/90 px-3 py-1 text-xs font-semibold text-ink">
          {destination.region}
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
