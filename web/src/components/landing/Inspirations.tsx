import { useState } from "react";
import { CONSEILLERS, INSPIRATIONS } from "../../data/detourContent";
import type { Destination } from "../../data/detourContent";
import { DestinationCard } from "./DestinationCard";

interface InspirationsProps {
  onDecrir: () => void;
}

/** Section « Inspirations du moment » + détail fictif via modal « Découvrir ». */
export function Inspirations({ onDecrir }: InspirationsProps) {
  const [detail, setDetail] = useState<Destination | null>(null);

  return (
    <section id="inspirations" className="scroll-mt-20 bg-[#f2f7fc] py-16 lg:py-24">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="max-w-2xl">
          <p className="mb-2 text-sm font-semibold uppercase tracking-widest text-[#38bdb8]">
            {INSPIRATIONS.surtitre}
          </p>
          <h2 className="text-3xl font-bold text-[#0b2447] sm:text-4xl">{INSPIRATIONS.titre}</h2>
          <p className="mt-4 text-[#4b6480]">{INSPIRATIONS.texte}</p>
        </div>

        <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {INSPIRATIONS.destinations.map((d) => (
            <DestinationCard key={d.id} destination={d} onDecouvrir={setDetail} />
          ))}
        </div>
      </div>

      {detail && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="detail-titre"
        >
          <div className="absolute inset-0 bg-[#07101e]/70" onClick={() => setDetail(null)} />
          <div className="relative max-h-[90vh] w-full max-w-lg overflow-auto rounded-2xl bg-white p-6 shadow-2xl sm:p-8">
            <button
              onClick={() => setDetail(null)}
              className="absolute right-4 top-4 rounded-full p-2 text-[#4b6480] outline-none hover:bg-[#f2f7fc] focus-visible:ring-2 focus-visible:ring-[#38bdb8]"
              aria-label="Fermer le détail"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5} aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
              </svg>
            </button>
            <p className="text-sm font-semibold uppercase tracking-widest text-[#38bdb8]">
              Inspiration fictive
            </p>
            <h3 id="detail-titre" className="mt-2 text-2xl font-bold text-[#0b2447]">
              {detail.titre}
            </h3>
            <p className="mt-1 text-sm font-semibold text-[#4b6480]">
              {detail.region} · {detail.prixIndicatif}
            </p>
            <p className="mt-4 leading-relaxed text-[#4b6480]">{detail.description}</p>
            <div className="mt-6 rounded-xl bg-[#f0eefe] p-4 text-sm text-[#4b3a8f]">
              {CONSEILLERS.disponibilite.jours}, {CONSEILLERS.disponibilite.heures} · réponse{" "}
              {CONSEILLERS.disponibilite.delai}. Aucune réservation réelle : un conseiller prépare
              une proposition, vous décidez ensuite.
            </div>
            <button
              onClick={() => {
                setDetail(null);
                onDecrir();
              }}
              className="mt-6 w-full rounded-full bg-[#0b2447] px-6 py-3 text-base font-semibold text-white outline-none transition hover:bg-[#12335e] focus-visible:ring-2 focus-visible:ring-[#38bdb8] focus-visible:ring-offset-2"
            >
              Décrire mon voyage
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
