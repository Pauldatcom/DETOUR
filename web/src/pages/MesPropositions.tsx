import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { PropositionCard } from "../components/PropositionCard";
import { api } from "../lib/api";
import type { Proposition } from "../types";

export function MesPropositions() {
  const [propositions, setPropositions] = useState<Proposition[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    api
      .mesPropositions()
      .then(({ propositions: results }) => {
        if (!cancelled) setPropositions(results);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Erreur de chargement.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section aria-labelledby="propositions-heading">
      <h2 id="propositions-heading" className="text-xl font-bold sm:text-2xl">
        Mes propositions
      </h2>
      <p className="mt-1 text-sm text-ballast">
        Consultez les propositions préparées par votre conseiller.
      </p>

      {loading && <p className="mt-8 text-sm text-ballast">Chargement de vos propositions…</p>}

      {error && (
        <p role="alert" className="mt-8 rounded-xl bg-brick/5 px-4 py-3 text-sm text-brick">
          {error}
        </p>
      )}

      {!loading && !error && propositions.length === 0 && (
        <div className="mt-6 rounded-2xl border border-line bg-card p-10 text-center">
          <h3 className="text-lg font-bold">Aucune proposition pour le moment</h3>
          <p className="mt-2 text-sm text-ballast">
            Après l’envoi d’une demande, un conseiller préparera une proposition de voyage.
          </p>
          <Link
            to="/mon-compte/demandes"
            className="mt-5 inline-block rounded-full border border-line px-5 py-2 text-sm font-semibold text-ink outline-none hover:border-ink focus-visible:ring-2 focus-visible:ring-yellow"
          >
            Voir mes demandes
          </Link>
        </div>
      )}

      {!loading && !error && propositions.length > 0 && (
        <div className="mt-6 grid gap-6 lg:grid-cols-2">
          {propositions.map((proposition) => (
            <PropositionCard key={proposition.id} proposition={proposition} />
          ))}
        </div>
      )}
    </section>
  );
}
