import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../lib/api";
import { formatDate, formatEuro } from "../lib/format";
import type { Demande } from "../types";

const STATUTS: Record<string, string> = {
  nouvelle: "Nouvelle",
  a_analyser: "À analyser",
  a_revoir: "À revoir",
  propose: "Proposition en préparation",
  valide: "Validée",
  refuse: "Refusée",
};

export function DemandeDetail() {
  const { id } = useParams<{ id: string }>();
  const [demande, setDemande] = useState<Demande | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    api
      .demande(id)
      .then(({ demande: result }) => {
        if (!cancelled) setDemande(result);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Demande introuvable.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  if (loading) return <p className="text-sm text-[#4b6480]">Chargement de votre demande…</p>;
  if (error || !demande) {
    return (
      <div>
        <p role="alert" className="rounded-xl bg-[#fff0f0] px-4 py-3 text-sm text-[#b91c1c]">
          {error || "Demande introuvable."}
        </p>
        <Link
          to="/mon-compte/demandes"
          className="mt-5 inline-block text-sm font-semibold text-[#0b2447] underline"
        >
          ← Retour à mes demandes
        </Link>
      </div>
    );
  }

  const voyage = demande.demande;
  return (
    <article>
      <Link
        to="/mon-compte/demandes"
        className="text-sm font-semibold text-[#0b2447] outline-none hover:text-[#159c98] focus-visible:ring-2 focus-visible:ring-[#38bdb8]"
      >
        ← Retour à mes demandes
      </Link>
      <div className="mt-5 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold">{voyage.destination}</h2>
          <p className="mt-1 text-sm text-[#4b6480]">
            Demande envoyée le {formatDate(demande.cree_le)}
          </p>
        </div>
        <span className="rounded-full bg-[#e9f9f8] px-3 py-1.5 text-sm font-semibold text-[#147f7c]">
          {STATUTS[demande.statut] ?? demande.statut}
        </span>
      </div>

      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        <Info
          label="Dates"
          value={`${formatDate(voyage.date_depart)} – ${formatDate(voyage.date_retour)}`}
        />
        <Info
          label="Voyageurs"
          value={`${voyage.nombre_voyageurs} personne${voyage.nombre_voyageurs > 1 ? "s" : ""}`}
        />
        <Info label="Type de voyage" value={voyage.type_voyage} />
        <Info
          label="Budget par personne (votre demande)"
          value={formatEuro(voyage.budget_max_par_personne)}
        />
        <Info label="Niveau d’aventure" value={voyage.niveau_aventure} />
        <Info label="Guide souhaité" value={voyage.besoin_guide ? "Oui" : "Pas nécessaire"} />
      </div>

      {(voyage.souhaits || voyage.contraintes || voyage.activites?.length > 0) && (
        <section className="mt-6 rounded-2xl border border-[#e8eef6] bg-white p-5">
          <h3 className="font-bold">Vos envies et contraintes</h3>
          {voyage.souhaits && (
            <p className="mt-3 text-sm whitespace-pre-wrap text-[#4b6480]">{voyage.souhaits}</p>
          )}
          {voyage.contraintes && (
            <p className="mt-3 text-sm whitespace-pre-wrap text-[#4b6480]">{voyage.contraintes}</p>
          )}
          {voyage.activites?.length > 0 && (
            <ul className="mt-3 flex flex-wrap gap-2">
              {voyage.activites.map((activite) => (
                <li
                  key={activite}
                  className="rounded-full bg-[#f2f7fc] px-3 py-1 text-xs text-[#334d6b]"
                >
                  {activite}
                </li>
              ))}
            </ul>
          )}
        </section>
      )}
    </article>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-[#e8eef6] bg-white p-4">
      <p className="text-xs font-semibold tracking-wide text-[#8ba8c4] uppercase">{label}</p>
      <p className="mt-1 font-medium text-[#0b2447]">{value || "—"}</p>
    </div>
  );
}
