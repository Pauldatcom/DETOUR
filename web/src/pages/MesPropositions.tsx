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

/** Page Mes propositions — espace voyageur, design clair. */
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
    <div className="min-h-screen bg-[#f7fafd] text-[#0b2447]">
      <PublicNav />
      <main className="mx-auto max-w-5xl px-4 py-12 sm:px-6 lg:py-16">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold sm:text-3xl">Mes propositions</h1>
            <p className="mt-1 text-sm text-[#4b6480]">
              {nom ? `Bonjour ${nom},` : "Bonjour,"} voici vos propositions de voyage.
            </p>
          </div>
          <button
            onClick={() => {
              void api.logout();
              onLogout();
            }}
            className="rounded-full border border-[#d5e0ee] px-4 py-2 text-sm font-semibold text-[#0b2447] transition outline-none hover:border-[#38bdb8] focus-visible:ring-2 focus-visible:ring-[#38bdb8]"
          >
            Déconnexion
          </button>
        </div>

        {loading && <p className="mt-8 text-[#4b6480]">Chargement…</p>}

        {error && (
          <div className="mt-8 rounded-xl border border-[#fce8e8] bg-[#fff0f0] px-4 py-3 text-sm text-[#b91c1c]">
            {error}
          </div>
        )}

        {!loading && !error && props.length === 0 && (
          <div className="mt-8 rounded-2xl border border-[#e8eef6] bg-white p-12 text-center">
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-[#f0eefe]">
              <svg
                className="h-8 w-8 text-[#7a5cd6]"
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
            <p className="mt-2 text-sm text-[#4b6480]">
              Décrivez votre voyage et un conseiller vous préparera une proposition sous 24 à 48
              heures ouvrées.
            </p>
            <Link
              to="/accueil"
              className="mt-6 inline-block rounded-full bg-[#0b2447] px-6 py-2.5 text-sm font-semibold text-white transition outline-none hover:bg-[#12335e] focus-visible:ring-2 focus-visible:ring-[#38bdb8]"
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
