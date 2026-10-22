import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { formatDate } from "../lib/format";
import type { Demande } from "../types";

const STATUTS: Record<string, string> = {
  nouvelle: "Nouvelle",
  a_analyser: "À analyser",
  a_revoir: "À revoir",
  propose: "Proposition en préparation",
  valide: "Validée",
  refuse: "Refusée",
};

export function MesDemandes() {
  const [demandes, setDemandes] = useState<Demande[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    api
      .mesDemandes()
      .then(({ demandes: results }) => {
        if (!cancelled) setDemandes(results);
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
    <section aria-labelledby="demandes-heading">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 id="demandes-heading" className="text-xl font-bold sm:text-2xl">
            Mes demandes
          </h2>
          <p className="mt-1 text-sm text-[#4b6480]">
            Retrouvez vos voyages et suivez leur avancement.
          </p>
        </div>
        <Link
          to="/accueil"
          className="rounded-full bg-[#0b2447] px-5 py-2.5 text-sm font-semibold text-white transition outline-none hover:bg-[#12335e] focus-visible:ring-2 focus-visible:ring-[#38bdb8]"
        >
          Nouvelle demande
        </Link>
      </div>

      {loading && <p className="mt-8 text-sm text-[#4b6480]">Chargement de vos demandes…</p>}

      {error && (
        <p role="alert" className="mt-8 rounded-xl bg-[#fff0f0] px-4 py-3 text-sm text-[#b91c1c]">
          {error}
        </p>
      )}

      {!loading && !error && demandes.length === 0 && (
        <div className="mt-8 rounded-2xl border border-[#e8eef6] bg-white px-6 py-12 text-center">
          <div className="mx-auto grid h-14 w-14 place-items-center rounded-full bg-[#e9f9f8] text-[#159c98]">
            <svg
              className="h-7 w-7"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.6}
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M8.25 6.75h12m-12 5.25h12m-12 5.25h8.25M3.75 6.75h.008v.008H3.75V6.75Zm0 5.25h.008v.008H3.75V12Zm0 5.25h.008v.008H3.75v-.008Z"
              />
            </svg>
          </div>
          <h3 className="mt-4 text-lg font-bold">Vous n’avez pas encore de demande</h3>
          <p className="mt-2 text-sm text-[#4b6480]">
            Décrivez votre projet de voyage et retrouvez son suivi ici.
          </p>
          <Link
            to="/accueil"
            className="mt-5 inline-block rounded-full border border-[#d5e0ee] px-5 py-2 text-sm font-semibold text-[#0b2447] outline-none hover:border-[#38bdb8] focus-visible:ring-2 focus-visible:ring-[#38bdb8]"
          >
            Décrire mon voyage
          </Link>
        </div>
      )}

      {!loading && !error && demandes.length > 0 && (
        <ul className="mt-6 grid gap-4">
          {demandes.map((demande) => (
            <li key={demande.id}>
              <Link
                to={`/mon-compte/demandes/${demande.id}`}
                className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-[#e8eef6] bg-white p-5 shadow-sm transition outline-none hover:border-[#b5e8e5] hover:shadow-md focus-visible:ring-2 focus-visible:ring-[#38bdb8]"
              >
                <div>
                  <h3 className="font-bold">{demande.demande.destination || "Voyage à définir"}</h3>
                  <p className="mt-1 text-sm text-[#4b6480]">
                    {demande.demande.date_depart} – {demande.demande.date_retour}
                    {demande.demande.nombre_voyageurs
                      ? ` · ${demande.demande.nombre_voyageurs} voyageur${demande.demande.nombre_voyageurs > 1 ? "s" : ""}`
                      : ""}
                  </p>
                  <p className="mt-1 text-xs text-[#8ba8c4]">
                    Envoyée le {formatDate(demande.cree_le)}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="rounded-full bg-[#e9f9f8] px-3 py-1 text-xs font-semibold text-[#147f7c]">
                    {STATUTS[demande.statut] ?? demande.statut}
                  </span>
                  <span aria-hidden="true" className="text-lg text-[#8ba8c4]">
                    →
                  </span>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
