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

/** Page Conseillers — profils, disponibilité, fonctionnement, CTA (2026 brand). */
export function ConseillersPage({ isLoggedIn, session, onLogout }: ConseillersPageProps) {
  const [formOuvert, setFormOuvert] = useState(false);

  return (
    <div className="min-h-screen bg-chalk text-ink">
      <PublicNav session={session} onLogout={onLogout} />
      <main>
        {/* Hero page */}
        <section className="bg-ink py-16 text-chalk lg:py-24">
          <div className="mx-auto max-w-6xl px-4 sm:px-6">
            <p className="mb-2 font-mono text-xs font-semibold tracking-widest text-sky uppercase">
              {CONSEILLERS.surtitre}
            </p>
            <h1 className="text-3xl font-extrabold sm:text-4xl">{CONSEILLERS.titre}</h1>
            <p className="mt-4 max-w-2xl text-sky">{CONSEILLERS.texte}</p>
          </div>
        </section>

        {/* Profils */}
        <section className="py-16 lg:py-20">
          <div className="mx-auto max-w-6xl px-4 sm:px-6">
            <h2 className="text-2xl font-extrabold">L'équipe</h2>
            <p className="mt-2 text-sm text-ballast">
              Exemples fictifs — ces profils illustrent le rôle d'un conseiller DÉTOUR.
            </p>
            <div className="mt-10 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
              {CONSEILLERS.profils.map((p) => (
                <article
                  key={p.id}
                  className="rounded-2xl border border-line bg-card p-6 shadow-sm"
                >
                  <div
                    className="flex h-16 w-16 items-center justify-center rounded-full text-2xl font-extrabold text-chalk"
                    style={{ background: "linear-gradient(135deg, #16233f, #bcd3ea)" }}
                    aria-hidden="true"
                  >
                    {p.prenom[0]}
                  </div>
                  <h3 className="mt-4 text-lg font-extrabold">{p.prenom}</h3>
                  <p className="mt-1 font-mono text-xs font-semibold tracking-wide text-ballast uppercase">
                    {p.specialite}
                  </p>
                  <p className="mt-3 text-sm leading-relaxed text-ballast">{p.bio}</p>
                  <div className="mt-4 rounded-xl bg-sky/40 px-4 py-2 text-xs text-ink">
                    Disponible : {p.disponibilite}
                  </div>
                </article>
              ))}
            </div>
          </div>
        </section>

        {/* Disponibilité */}
        <section className="bg-card py-16 lg:py-20">
          <div className="mx-auto max-w-6xl px-4 sm:px-6">
            <div className="grid gap-8 lg:grid-cols-3">
              <div className="rounded-2xl border border-line bg-chalk p-6 text-center">
                <p className="font-mono text-xs font-semibold tracking-widest text-ballast uppercase">
                  Disponibles
                </p>
                <p className="mt-2 text-lg font-extrabold">{CONSEILLERS.disponibilite.jours}</p>
              </div>
              <div className="rounded-2xl border border-line bg-chalk p-6 text-center">
                <p className="font-mono text-xs font-semibold tracking-widest text-ballast uppercase">
                  Horaires
                </p>
                <p className="mt-2 text-lg font-extrabold">{CONSEILLERS.disponibilite.heures}</p>
              </div>
            </div>
            <p className="mt-6 text-center text-sm text-ballast">
              {CONSEILLERS.disponibilite.precision}
            </p>
          </div>
        </section>

        {/* Comment ça marche (rappel compact) */}
        <section className="py-16 lg:py-20">
          <div className="mx-auto max-w-6xl px-4 sm:px-6">
            <p className="mb-2 font-mono text-xs font-semibold tracking-widest text-ballast uppercase">
              {COMMENT_CA_MARCHE.surtitre}
            </p>
            <h2 className="text-2xl font-extrabold">{COMMENT_CA_MARCHE.titre}</h2>
            <div className="mt-10 grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
              {COMMENT_CA_MARCHE.etapes.map((etape) => (
                <div key={etape.id} className="relative">
                  <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-sky/50">
                    <span className="text-xl font-extrabold text-ink">{etape.numero}</span>
                  </div>
                  <h3 className="mt-4 text-lg font-extrabold">{etape.titre}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-ballast">{etape.texte}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="bg-ink py-16 text-chalk lg:py-20">
          <div className="mx-auto max-w-2xl px-4 text-center sm:px-6">
            <h2 className="text-2xl font-extrabold sm:text-3xl">Prêt à décrire votre voyage ?</h2>
            <p className="mt-4 text-sky">Aucune réservation réelle — vous gardez la main.</p>
            <button
              onClick={() => setFormOuvert(true)}
              className="mt-8 rounded-full bg-yellow px-8 py-3 font-semibold text-base text-ink shadow-lg transition hover:bg-yellow/90"
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
