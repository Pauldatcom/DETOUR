import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { PropositionCard } from "../components/PropositionCard";
import { api } from "../lib/api";
import type { Proposition } from "../types";

/** Single proposal page — restores navigation from the card list. */
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
    <main className="min-h-screen bg-[#f7fafd] px-4 py-8">
      <div className="mx-auto max-w-2xl">
        <Link
          to="/mes-propositions"
          className="text-sm font-medium text-[#0b2447] outline-none hover:text-[#38bdb8] focus-visible:ring-2 focus-visible:ring-[#38bdb8]"
        >
          ← Mes propositions
        </Link>
        {loading && <p className="mt-8 text-sm text-[#4b6480]">Chargement…</p>}
        {error && (
          <p role="alert" className="mt-8 text-sm text-[#b91c1c]">
            {error}
          </p>
        )}
        {prop && !loading && (
          <div className="mt-6">
            <PropositionCard proposition={prop} linked={false} />
          </div>
        )}
      </div>
    </main>
  );
}
