import { Link } from "react-router-dom";
import type { ChangementLecture, ContrainteVerifiee, Prestation, Proposition } from "../types";
import {
  PROP_STATUT_LABELS,
  STATUT_COLORS,
  formatEuro,
  formatDate,
  formatDateTime,
} from "../lib/format";

interface PropositionCardProps {
  proposition: Proposition;
  /** When false, render as a static article (detail page). Default: linked list card. */
  linked?: boolean;
}

/** One prestation line: verified price + source/time, or missing (never invented). */
function PrestationLine({ item }: { item: Prestation }) {
  if (item.verification !== "verifie") {
    return (
      <li className="text-sm text-ballast">
        <span className="font-medium text-ink">{item.nom}</span>
        <span className="text-ballast/60"> ({item.id})</span>
        <span> — prix non vérifié</span>
        {item.copie_depuis_v1 && (
          <span className="text-ballast/60"> · repris de v1 (non relu)</span>
        )}
      </li>
    );
  }
  return (
    <li className="text-sm text-ballast">
      <span className="font-medium text-ink">{item.nom}</span>
      <span className="text-ballast/60"> ({item.id})</span>
      <span className="meta-nowrap">
        {" "}
        — {formatEuro(item.prix_unitaire_eur ?? 0)} / pers
        {item.disponible === false ? " · indisponible" : " · disponible"}
      </span>
      <div className="meta-nowrap mt-0.5 text-xs text-ballast/60">
        {item.source} · {formatDateTime(item.consulte_le ?? "")}
        {item.copie_depuis_v1 && " · repris de v1 (non relu)"}
      </div>
    </li>
  );
}

const CONTRAINTE_MARQUE: Record<ContrainteVerifiee["statut"], string> = {
  ok: "✅",
  a_verifier: "⚠️",
  non_respectee: "❌",
};

/** One program-checked customer constraint (#41). */
function ContrainteLine({ item }: { item: ContrainteVerifiee }) {
  return (
    <li className="text-xs text-ballast">
      {CONTRAINTE_MARQUE[item.statut]} {item.detail}
    </li>
  );
}

/** Newer reading vs v1: previous/new price, unavailable, or unchanged. */
function ChangementLine({ item }: { item: ChangementLecture }) {
  if (item.inchange) {
    return <li className="text-xs text-ballast/60">{item.nom}: prix et disponibilité inchangés</li>;
  }
  return (
    <li className="text-xs text-ballast">
      {item.nom}
      {item.prix_change && (
        <>
          : {formatEuro(item.prix_avant)} →{" "}
          <span className="font-semibold text-brick">{formatEuro(item.prix_apres)}</span>
        </>
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
          <h3 className="font-extrabold text-ink">{prop.titre}</h3>
          <p className="mt-1 line-clamp-2 text-sm text-ballast">{prop.description}</p>
        </div>
        <span
          className={`inline-flex items-center rounded-full border border-line px-2.5 py-0.5 text-xs font-semibold ${
            STATUT_COLORS[prop.statut] ?? "text-ballast"
          }`}
        >
          {PROP_STATUT_LABELS[prop.statut] ?? prop.statut}
        </span>
      </div>

      {prop.prestations.length > 0 && (
        <ul className="mt-4 space-y-2 border-t border-line pt-3">
          {prop.prestations.map((item) => (
            <PrestationLine key={item.id} item={item} />
          ))}
        </ul>
      )}

      {prop.contraintes_verifiees && prop.contraintes_verifiees.length > 0 && (
        <ul className="mt-3 space-y-1 border-t border-dashed border-line pt-3">
          <li className="text-xs font-semibold text-ink">Contraintes prises en compte</li>
          {prop.contraintes_verifiees.map((item) => (
            <ContrainteLine key={item.contrainte} item={item} />
          ))}
        </ul>
      )}

      {prop.changements && prop.changements.length > 0 && (
        <ul className="mt-3 space-y-1 border-t border-dashed border-line pt-3">
          <li className="text-xs font-semibold text-ink">Nouvelle lecture</li>
          {prop.changements.map((item) => (
            <ChangementLine key={item.id} item={item} />
          ))}
        </ul>
      )}

      <div className="mt-4 flex flex-col gap-3 border-t border-line pt-3 sm:flex-row sm:items-end sm:justify-between">
        <div className="meta-nowrap flex flex-wrap gap-2 text-xs text-ballast/60">
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
        <div className="sm:text-right">
          <span className="meta-nowrap font-extrabold text-ink">
            {formatEuro(prop.prix_total_eur)}
          </span>
          {manquantes > 0 && (
            <p className="mt-0.5 text-[10px] text-ballast/60">
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
      <article className="rounded-2xl border border-line bg-card p-5 shadow-sm">{body}</article>
    );
  }

  return (
    <Link
      to={`/mon-compte/propositions/${prop.id}`}
      className="block rounded-2xl border border-line bg-card p-5 shadow-sm transition outline-none hover:-translate-y-0.5 hover:shadow-lg"
    >
      {body}
    </Link>
  );
}
