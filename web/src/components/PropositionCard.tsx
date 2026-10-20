import { Link } from "react-router-dom";
import type { Proposition } from "../types";
import { PROP_STATUT_LABELS, STATUT_COLORS, formatEuro, formatDate } from "../lib/format";

interface PropositionCardProps {
  proposition: Proposition;
}

/** Carte proposition — design clair (matching landing). */
export function PropositionCard({ proposition: prop }: PropositionCardProps) {
  return (
    <Link
      to={`/propositions/${prop.id}`}
      className="block rounded-2xl border border-[#e8eef6] bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-lg"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="font-bold text-[#0b2447]">{prop.titre}</h3>
          <p className="mt-1 line-clamp-2 text-sm text-[#4b6480]">
            {prop.description}
          </p>
        </div>
        <span
          className={`inline-flex items-center rounded-full border border-[#e8eef6] px-2.5 py-0.5 text-xs font-semibold ${
            (STATUT_COLORS[prop.statut] ?? "text-[#8ba8c4]")
          }`}
        >
          {(PROP_STATUT_LABELS[prop.statut] ?? prop.statut)}
        </span>
      </div>
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
        <span className="font-bold text-[#38bdb8]">
          {formatEuro(prop.prix_total_eur)}
        </span>
      </div>
    </Link>
  );
}