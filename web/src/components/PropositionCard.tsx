import { Link } from "react-router-dom";
import type { ChangementLecture, Prestation, Proposition } from "../types";
import { PROP_STATUT_LABELS, STATUT_COLORS, formatEuro, formatDate, formatDateTime } from "../lib/format";

interface PropositionCardProps {
  proposition: Proposition;
  /** When false, render as a static article (detail page). Default: linked list card. */
  linked?: boolean;
}

/** One prestation line: verified price + source/time, or missing (never invented). */
function PrestationLine({ item }: { item: Prestation }) {
  if (item.verification !== "verifie") {
    return (
      <li className="text-sm text-[#4b6480]">
        <span className="font-medium text-[#0b2447]">{item.nom}</span>
        <span className="text-[#8ba8c4]"> ({item.id})</span>
        <span> — manquant</span>
        {item.copie_depuis_v1 && (
          <span className="text-[#8ba8c4]"> · repris de v1 (non relu)</span>
        )}
      </li>
    );
  }
  return (
    <li className="text-sm text-[#4b6480]">
      <span className="font-medium text-[#0b2447]">{item.nom}</span>
      <span className="text-[#8ba8c4]"> ({item.id})</span>
      <span>
        {" "}
        — {formatEuro(item.prix_unitaire_eur ?? 0)} / pers
        {item.disponible === false ? " · indisponible" : " · disponible"}
      </span>
      <div className="mt-0.5 text-xs text-[#8ba8c4]">
        {item.source} · {formatDateTime(item.consulte_le ?? "")}
        {item.copie_depuis_v1 && " · repris de v1 (non relu)"}
      </div>
    </li>
  );
}

/** Newer reading vs v1: previous/new price, unavailable, or unchanged. */
function ChangementLine({ item }: { item: ChangementLecture }) {
  if (item.inchange) {
    return (
      <li className="text-xs text-[#8ba8c4]">
        {item.nom}: prix et disponibilité inchangés
      </li>
    );
  }
  return (
    <li className="text-xs text-[#4b6480]">
      {item.nom}
      {item.prix_change && (
        <>: {formatEuro(item.prix_avant)} → {formatEuro(item.prix_apres)}</>
      )}
      {!item.disponible_apres && <> · indisponible</>}
      {item.disponibilite_change && item.disponible_apres && <> · devenu disponible</>}
    </li>
  );
}

/** Proposal card: title, total, and each line with its source and read time. */
export function PropositionCard({ proposition: prop, linked = true }: PropositionCardProps) {
  const manquantes = prop.prestations.filter((p) => p.verification !== "verifie").length;
  const body = (
    <>
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="font-bold text-[#0b2447]">{prop.titre}</h3>
          <p className="mt-1 line-clamp-2 text-sm text-[#4b6480]">{prop.description}</p>
        </div>
        <span
          className={`inline-flex items-center rounded-full border border-[#e8eef6] px-2.5 py-0.5 text-xs font-semibold ${
            STATUT_COLORS[prop.statut] ?? "text-[#8ba8c4]"
          }`}
        >
          {PROP_STATUT_LABELS[prop.statut] ?? prop.statut}
        </span>
      </div>

      {prop.prestations.length > 0 && (
        <ul className="mt-4 space-y-2 border-t border-[#e8eef6] pt-3">
          {prop.prestations.map((item) => (
            <PrestationLine key={item.id} item={item} />
          ))}
        </ul>
      )}

      {prop.changements && prop.changements.length > 0 && (
        <ul className="mt-3 space-y-1 border-t border-dashed border-[#e8eef6] pt-3">
          <li className="text-xs font-semibold text-[#0b2447]">Nouvelle lecture</li>
          {prop.changements.map((item) => (
            <ChangementLine key={item.id} item={item} />
          ))}
        </ul>
      )}

      <div className="mt-4 flex items-center justify-between border-t border-[#e8eef6] pt-3">
        <div className="flex flex-wrap gap-2 text-xs text-[#8ba8c4]">
          <span>{prop.prestations.length} prestations</span>
          <span>·</span>
          <span>{formatDate(prop.cree_le)}</span>
          {prop.conseiller && (
            <>
              <span>·</span>
              <span>par {prop.conseiller}</span>
            </>
          )}
        </div>
        <div className="text-right">
          <span className="font-bold text-[#38bdb8]">{formatEuro(prop.prix_total_eur)}</span>
          {manquantes > 0 && (
            <p className="mt-0.5 text-[10px] text-[#8ba8c4]">
              {manquantes > 1
                ? `total vérifié · ${manquantes} lignes non vérifiées`
                : "total vérifié · 1 ligne non vérifiée"}
            </p>
          )}
        </div>
      </div>
    </>
  );

  if (!linked) {
    return (
      <article className="rounded-2xl border border-[#e8eef6] bg-white p-5 shadow-sm">{body}</article>
    );
  }

  return (
    <Link
      to={`/propositions/${prop.id}`}
      className="block rounded-2xl border border-[#e8eef6] bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-lg outline-none focus-visible:ring-2 focus-visible:ring-[#38bdb8]"
    >
      {body}
    </Link>
  );
}
