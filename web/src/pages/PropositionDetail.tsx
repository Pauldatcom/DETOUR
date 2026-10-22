import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { PropositionCard } from "../components/PropositionCard";
import { api } from "../lib/api";
import type { Proposition } from "../types";

/** Single proposal page — restores navigation from the card list, 2026 brand. */
export function PropositionDetail() {
  const { id } = useParams<{ id: string }>();
  const [prop, setProp] = useState<Proposition | null>(null);
  const [error, setError] = useState("");
  const [readyFor, setReadyFor] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    api
      .proposition(id)
      .then((data) => {
        if (cancelled) return;
        setProp(data.proposition);
        setError("");
        setReadyFor(id);
      })
      .catch((err) => {
        if (cancelled) return;
        setProp(null);
        setError(err instanceof Error ? err.message : "Proposition introuvable.");
        setReadyFor(id);
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  const loading = Boolean(id) && readyFor !== id;

  return (
    <main id="contenu-principal" className="min-h-screen bg-chalk px-4 py-8">
      <div className="mx-auto max-w-2xl">
        <Link
          to="/mon-compte/propositions"
          className="text-sm font-medium text-ink hover:text-ballast"
        >
          ← Mes propositions
        </Link>
        {loading && <p className="mt-8 text-sm text-ballast">Chargement…</p>}
        {error && (
          <p role="alert" className="mt-8 text-sm text-brick">
            {error}
          </p>
        )}
        {prop && !loading && (
          <div className="mt-6">
            <header className="mb-6">
              <p className="font-mono text-xs tracking-widest text-ballast uppercase">
                Proposition de voyage
              </p>
              <h1 className="mt-2 text-3xl font-extrabold sm:text-4xl">{prop.titre}</h1>
              <p className="mt-2 text-ballast">{prop.description}</p>
              {prop.conseiller && (
                <p className="mt-2 text-sm text-ballast">
                  Préparée par <span className="font-semibold text-ink">{prop.conseiller}</span>
                </p>
              )}
            </header>
            <PropositionCard proposition={prop} linked={false} />
          </div>
        )}
      </div>
    </main>
  );
}
