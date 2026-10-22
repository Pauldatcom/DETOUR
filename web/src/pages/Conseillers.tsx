import { useState } from "react";
import { PublicNav } from "../components/landing/PublicNav";
import { Footer } from "../components/landing/Footer";
import { TravelRequestForm } from "../components/landing/TravelRequestForm";
import { ChatWidget } from "../components/landing/ChatWidget";
import { CONSEILLERS, COMMENT_CA_MARCHE } from "../data/detourContent";
import type { Session } from "../types";

interface ConseillersPageProps {
  isLoggedIn: boolean;
  session: Session | null;
  onLogout: () => Promise<void>;
}

/** Page Conseillers — profils, disponibilité, fonctionnement, CTA. */
export function ConseillersPage({ isLoggedIn, session, onLogout }: ConseillersPageProps) {
  const [formOuvert, setFormOuvert] = useState(false);

  return (
    <div className="min-h-screen bg-white text-[#0b2447]">
      <PublicNav session={session} onLogout={onLogout} />
      <main>
        {/* Hero page */}
        <section className="bg-[#0b2447] py-16 text-white lg:py-24">
          <div className="mx-auto max-w-6xl px-4 sm:px-6">
            <p className="mb-2 text-sm font-semibold tracking-widest text-[#7fd9d5] uppercase">
              {CONSEILLERS.surtitre}
            </p>
            <h1 className="text-3xl font-bold sm:text-4xl">{CONSEILLERS.titre}</h1>
            <p className="mt-4 max-w-2xl text-[#c9d9ec]">{CONSEILLERS.texte}</p>
          </div>
        </section>

        {/* Profils */}
        <section className="py-16 lg:py-20">
          <div className="mx-auto max-w-6xl px-4 sm:px-6">
            <h2 className="text-2xl font-bold">L'équipe</h2>
            <p className="mt-2 text-sm text-[#4b6480]">
              Exemples fictifs — ces profils illustrent le rôle d'un conseiller DÉTOUR.
            </p>
            <div className="mt-10 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
              {CONSEILLERS.profils.map((p) => (
                <article
                  key={p.id}
                  className="rounded-2xl border border-[#e8eef6] bg-white p-6 shadow-sm"
                >
                  <div
                    className="flex h-16 w-16 items-center justify-center rounded-full text-2xl font-bold text-white"
                    style={{
                      background: "linear-gradient(135deg, #38bdb8, #7a5cd6)",
                    }}
                    aria-hidden="true"
                  >
                    {p.prenom[0]}
                  </div>
                  <h3 className="mt-4 text-lg font-bold">{p.prenom}</h3>
                  <p className="mt-1 text-sm font-semibold text-[#38bdb8]">{p.specialite}</p>
                  <p className="mt-3 text-sm leading-relaxed text-[#4b6480]">{p.bio}</p>
                  <div className="mt-4 rounded-xl bg-[#f2f7fc] px-4 py-2 text-xs text-[#4b6480]">
                    Disponible : {p.disponibilite}
                  </div>
                </article>
              ))}
            </div>
          </div>
        </section>

        {/* Disponibilité */}
        <section className="bg-[#f2f7fc] py-16 lg:py-20">
          <div className="mx-auto max-w-6xl px-4 sm:px-6">
            <div className="grid gap-8 lg:grid-cols-3">
              <div className="rounded-2xl border border-[#e8eef6] bg-white p-6 text-center">
                <p className="text-xs font-semibold tracking-widest text-[#38bdb8] uppercase">
                  Disponibles
                </p>
                <p className="mt-2 text-lg font-bold">{CONSEILLERS.disponibilite.jours}</p>
              </div>
              <div className="rounded-2xl border border-[#e8eef6] bg-white p-6 text-center">
                <p className="text-xs font-semibold tracking-widest text-[#38bdb8] uppercase">
                  Horaires
                </p>
                <p className="mt-2 text-lg font-bold">{CONSEILLERS.disponibilite.heures}</p>
              </div>
              <div className="rounded-2xl border border-[#e8eef6] bg-white p-6 text-center">
                <p className="text-xs font-semibold tracking-widest text-[#38bdb8] uppercase">
                  Délai de réponse
                </p>
                <p className="mt-2 text-lg font-bold">{CONSEILLERS.disponibilite.delai}</p>
              </div>
            </div>
            <p className="mt-6 text-center text-sm text-[#4b6480]">
              {CONSEILLERS.disponibilite.precision}
            </p>
          </div>
        </section>

        {/* Comment ça marche (rappel compact) */}
        <section className="py-16 lg:py-20">
          <div className="mx-auto max-w-6xl px-4 sm:px-6">
            <p className="mb-2 text-sm font-semibold tracking-widest text-[#38bdb8] uppercase">
              {COMMENT_CA_MARCHE.surtitre}
            </p>
            <h2 className="text-2xl font-bold">{COMMENT_CA_MARCHE.titre}</h2>
            <div className="mt-10 grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
              {COMMENT_CA_MARCHE.etapes.map((etape) => (
                <div key={etape.id} className="relative">
                  <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[#f0eefe]">
                    <span className="text-xl font-bold text-[#7a5cd6]">{etape.numero}</span>
                  </div>
                  <h3 className="mt-4 text-lg font-bold">{etape.titre}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-[#4b6480]">{etape.texte}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="bg-[#0b2447] py-16 text-white lg:py-20">
          <div className="mx-auto max-w-2xl px-4 text-center sm:px-6">
            <h2 className="text-2xl font-bold sm:text-3xl">Prêt à décrire votre voyage ?</h2>
            <p className="mt-4 text-[#c9d9ec]">
              Un conseiller vous répond sous 24 à 48 heures ouvrées. Aucune réservation réelle —
              vous gardez la main.
            </p>
            <button
              onClick={() => setFormOuvert(true)}
              className="mt-8 rounded-full bg-white px-8 py-3 font-semibold text-[#0b2447] text-base shadow-lg transition outline-none hover:bg-[#eaf4fb] focus-visible:ring-2 focus-visible:ring-[#38bdb8] focus-visible:ring-offset-2 focus-visible:ring-offset-[#0b2447]"
            >
              Décrire mon voyage
            </button>
          </div>
        </section>
      </main>
      <Footer />

      {formOuvert && (
        <TravelRequestForm isLoggedIn={isLoggedIn} onClose={() => setFormOuvert(false)} />
      )}

      <ChatWidget isLoggedIn={isLoggedIn} />
    </div>
  );
}
