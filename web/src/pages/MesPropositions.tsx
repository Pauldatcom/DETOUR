import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { PublicNav } from "../components/landing/PublicNav";
import { Footer } from "../components/landing/Footer";
import { PropositionCard } from "../components/PropositionCard";
import { api } from "../lib/api";
import type { Proposition } from "../types";

interface MesPropositionsProps {
  nom?: string;
  onLogout: () => void;
}

/** Page Mes propositions — espace voyageur, 2026 brand (chalk/ink). */
export function MesPropositions({ nom, onLogout }: MesPropositionsProps) {
  const [props, setProps] = useState<Proposition[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .mesPropositions()
      .then((d) => setProps(d.propositions))
      .catch((err) => setError(err instanceof Error ? err.message : "Erreur"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-chalk text-ink">
      <PublicNav />
      <main className="mx-auto max-w-5xl px-4 py-12 sm:px-6 lg:py-16">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-extrabold sm:text-4xl">Mes propositions</h1>
            <p className="mt-1 text-sm text-ballast">
              {nom ? `Bonjour ${nom},` : "Bonjour,"} voici vos propositions de voyage.
            </p>
          </div>
          <button
            onClick={() => {
              void api.logout();
              onLogout();
            }}
            className="rounded-full border border-line px-4 py-2 text-sm font-semibold text-ink transition hover:border-ink focus-visible:ring-2 focus-visible:ring-yellow focus-visible:ring-offset-2"
          >
            Déconnexion
          </button>
        </div>

        {loading && <p className="mt-8 text-ballast">Chargement…</p>}

        {error && (
          <div className="mt-8 rounded-xl border border-brick/30 bg-brick/5 px-4 py-3 text-sm text-brick">
            {error}
          </div>
        )}

        {!loading && !error && props.length === 0 && (
          <div className="mt-8 rounded-2xl border border-line bg-card p-12 text-center">
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-sky/40">
              <svg
                className="h-8 w-8 text-ink"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={1.5}
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M9 6.75V15m6-6v8.25m-9-2.25h6m-6 3h6m9-12H3v18h18V3Z"
                />
              </svg>
            </div>
            <h2 className="text-lg font-bold">Aucune proposition pour le moment</h2>
            <p className="mt-2 text-sm text-ballast">
              Décrivez votre voyage et un conseiller vous préparera une proposition sous 24 à 48
              heures ouvrées.
            </p>
            <Link
              to="/accueil"
              className="mt-6 inline-block rounded-full bg-ink px-6 py-2.5 text-sm font-semibold text-chalk transition hover:bg-ink/85 focus-visible:ring-2 focus-visible:ring-yellow focus-visible:ring-offset-2"
            >
              Décrire mon voyage
            </Link>
          </div>
        )}

        {!loading && !error && props.length > 0 && (
          <div className="mt-8 grid gap-6 lg:grid-cols-2">
            {props.map((p) => (
              <PropositionCard key={p.id} proposition={p} />
            ))}
          </div>
        )}
      </main>
      <Footer />
    </div>
  );
}
