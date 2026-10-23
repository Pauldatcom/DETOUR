import { Link } from "react-router-dom";
import type { ChangementLecture, ContrainteVerifiee, Prestation, Proposition } from "../types";
import {
  PROP_STATUT_LABELS,
  STATUT_COLORS,
  derniereConfirmation,
  formatDate,
  formatDateTime,
} from "../lib/format";
import { advisorFirstName } from "../lib/tone";
import { PriceVerification, ProposalTotal } from "./traveler/PriceVerification";

interface PropositionCardProps {
  proposition: Proposition;
  /** When false, render as a static article (detail page). Default: linked list card. */
  linked?: boolean;
}

/** One prestation line: one of the five dated verification states (#127). */
function PrestationLine({ item, change }: { item: Prestation; change?: ChangementLecture }) {
  return (
    <li className="text-sm text-ballast">
      <span className="font-medium text-ink">{item.nom}</span>
      <PriceVerification service={item} change={change} compact showSource />
    </li>
  );
}

const CONTRAINTE_MARQUE: Record<ContrainteVerifiee["statut"], string> = {
  ok: "Respecté",
  a_verifier: "À confirmer",
  non_respectee: "Non respecté",
};

/** One program-checked customer constraint (#41). */
function ContrainteLine({ item }: { item: ContrainteVerifiee }) {
  return (
    <li className="text-xs text-ballast">
      {CONTRAINTE_MARQUE[item.statut]} · {item.detail}
    </li>
  );
}

/** Proposal card: title, total, and each line with its dated verification state. */
export function PropositionCard({ proposition: prop, linked = true }: PropositionCardProps) {
  const changes = new Map((prop.changements ?? []).map((change) => [change.id, change]));
  // The advisor confirms explicitly: the traveler sees who confirmed, when and why (#113).
  const confirmation = derniereConfirmation(prop.decisions_statut);
  const advisor = advisorFirstName(prop);
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

      {confirmation && (
        <div className="mt-3 rounded-xl border border-[#e8eef6] bg-[#f7fafd] p-3">
          <p className="text-xs font-semibold text-[#0b2447]">
            Confirmée par {confirmation.par} le {formatDateTime(confirmation.le)}
          </p>
          {confirmation.motif && (
            <p className="mt-1 text-xs text-[#4b6480]">« {confirmation.motif} »</p>
          )}
        </div>
      )}

      {prop.prestations.length > 0 && (
        <ul className="mt-4 space-y-2 border-t border-line pt-3">
          {prop.prestations.map((item) => (
            <PrestationLine key={item.id} item={item} change={changes.get(item.id)} />
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

      <div className="mt-4 flex flex-col gap-3 border-t border-line pt-3 sm:flex-row sm:items-end sm:justify-between">
        <div className="meta-nowrap flex flex-wrap gap-2 text-xs text-ballast/60">
          <span>{prop.prestations.length} prestations</span>
          <span>·</span>
          <span>{formatDate(prop.cree_le)}</span>
          {advisor && (
            <>
              <span>·</span>
              <span>par {advisor}</span>
            </>
          )}
        </div>
        <div className="sm:text-right">
          <ProposalTotal proposition={prop} />
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
