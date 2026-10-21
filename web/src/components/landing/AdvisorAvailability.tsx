import { useEffect, useState } from "react";
import { CONSEILLERS } from "../../data/detourContent";
import { api } from "../../lib/api";
import type { Disponibilite } from "../../types";

interface AdvisorAvailabilityProps {
  onDecrir: () => void;
}

/** Bloc disponibilité conseillers + engagements. */
export function AdvisorAvailability({ onDecrir }: AdvisorAvailabilityProps) {
  // #53 : the availability block reflects the advisor's real working hours.
  const [dispo, setDispo] = useState<Disponibilite | null>(null);

  useEffect(() => {
    let annule = false;
    api
      .disponibilite()
      .then((data) => {
        if (!annule) setDispo(data);
      })
      .catch(() => {
        /* Keep the static content in case the endpoint is unreachable. */
      });
    return () => {
      annule = true;
    };
  }, []);

  const fenetre = dispo?.fenetre;
  return (
    <section id="conseillers" className="scroll-mt-20 bg-[#0b2447] py-16 text-white lg:py-24">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute right-0 left-0"
        style={{
          background:
            "radial-gradient(800px 400px at 90% 50%, rgba(56,189,184,0.18), transparent 70%)",
        }}
      />
      <div className="relative mx-auto grid max-w-6xl gap-12 px-4 sm:px-6 lg:grid-cols-2 lg:items-center">
        <div>
          <p className="mb-2 text-sm font-semibold tracking-widest text-[#7fd9d5] uppercase">
            {CONSEILLERS.surtitre}
          </p>
          <h2 className="text-3xl font-bold sm:text-4xl">{CONSEILLERS.titre}</h2>
          <p className="mt-4 text-[#c9d9ec]">{CONSEILLERS.texte}</p>

          <div className="mt-8 grid gap-3 sm:grid-cols-3">
            <div className="rounded-xl border border-white/15 bg-white/5 p-4 text-center">
              <p className="text-xs text-[#7fd9d5]">Statut</p>
              <p className="mt-1 text-sm font-bold">
                {fenetre ? (fenetre.ouvert ? "Ouvert" : "Fermé") : "Disponibles"}
              </p>
            </div>
            <div className="rounded-xl border border-white/15 bg-white/5 p-4 text-center">
              <p className="text-xs text-[#7fd9d5]">Horaires</p>
              <p className="mt-1 text-sm font-bold">
                {fenetre?.prochaine_ouverture
                  ? new Date(fenetre.prochaine_ouverture).toLocaleString("fr-FR", {
                      weekday: "long",
                      hour: "2-digit",
                      minute: "2-digit",
                    })
                  : CONSEILLERS.disponibilite.heures}
              </p>
            </div>
            <div className="rounded-xl border border-white/15 bg-white/5 p-4 text-center">
              <p className="text-xs text-[#7fd9d5]">Délai de réponse</p>
              <p className="mt-1 text-sm font-bold">
                {fenetre?.echeance_cible
                  ? new Date(fenetre.echeance_cible).toLocaleString("fr-FR", {
                      dateStyle: "short",
                      timeStyle: "short",
                    })
                  : CONSEILLERS.disponibilite.delai}
              </p>
            </div>
          </div>
          <p className="mt-4 text-sm text-[#afc4dc]">
            {fenetre?.promesse_delai || CONSEILLERS.disponibilite.precision}
          </p>
        </div>

        <div>
          <ul className="space-y-4">
            {CONSEILLERS.engagements.map((e, i) => (
              <li key={i} className="flex items-start gap-3">
                <span
                  aria-hidden="true"
                  className="mt-1 flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-[#38bdb8]/20 text-[#38bdb8]"
                >
                  <svg
                    className="h-3.5 w-3.5"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2.5}
                    aria-hidden="true"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                  </svg>
                </span>
                <span className="text-[#c9d9ec]">{e}</span>
              </li>
            ))}
          </ul>
          <button
            onClick={onDecrir}
            className="mt-8 rounded-full bg-white px-8 py-3 font-semibold text-[#0b2447] text-base shadow-lg transition outline-none hover:bg-[#eaf4fb] focus-visible:ring-2 focus-visible:ring-[#38bdb8] focus-visible:ring-offset-2 focus-visible:ring-offset-[#0b2447]"
          >
            Décrire mon voyage
          </button>
        </div>
      </div>
    </section>
  );
}
