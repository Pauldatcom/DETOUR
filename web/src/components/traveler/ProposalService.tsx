import {
  formatAmount,
  perPersonSentence,
  priceCheckedSentence,
  seatsSentence,
} from "../../lib/tone";
import type { ChangementLecture, Prestation } from "../../types";

interface ProposalServiceProps {
  service: Prestation;
  seats: number | null;
  change?: ChangementLecture;
}

/** One service, said plainly: price per person, when it was checked, seats left. */
export function ProposalService({ service, seats, change }: ProposalServiceProps) {
  const verified = service.verification === "verifie";
  const fullyBooked = verified && service.disponible === false;
  const priceChanged = change && !change.inchange && change.prix_change;

  return (
    <li className="rounded-2xl border border-line bg-card p-5">
      <h4 className="font-display text-lg font-extrabold tracking-tight text-ink">{service.nom}</h4>

      {!verified && (
        <p className="mt-2 text-sm text-ballast">
          Prix et places en cours de vérification par votre conseiller.
        </p>
      )}

      {verified && fullyBooked && (
        <p className="mt-2 text-sm font-medium text-brick">
          {service.nom} est complet à cette date.
        </p>
      )}

      {verified && !fullyBooked && service.prix_unitaire_eur !== null && (
        <div className="mt-2 space-y-0.5 text-sm text-ink">
          <p className="font-semibold">{perPersonSentence(service.prix_unitaire_eur)}</p>
          {service.copie_depuis_v1 ? (
            <p className="text-ballast">
              Prix repris de la proposition précédente, en cours de revérification.
            </p>
          ) : (
            <p className="text-ballast">{priceCheckedSentence(service.consulte_le)}</p>
          )}
          {seats !== null && <p className="text-ballast">{seatsSentence(seats)}</p>}
          {service.prix_total_eur !== null && service.quantite > 1 && (
            <p className="text-ballast">
              {formatAmount(service.prix_total_eur)} au total pour ce poste.
            </p>
          )}
        </div>
      )}

      {priceChanged && (
        <p className="mt-3 rounded-lg bg-brick/10 px-3 py-2 text-sm text-brick">
          Le prix a changé depuis : {formatAmount(change.prix_avant)} →{" "}
          {formatAmount(change.prix_apres)} par personne. Votre conseiller vous en reparle.
        </p>
      )}
    </li>
  );
}
