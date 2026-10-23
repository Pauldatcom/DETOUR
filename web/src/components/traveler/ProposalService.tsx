import type { ChangementLecture, Prestation } from "../../types";
import { PriceVerification } from "./PriceVerification";

interface ProposalServiceProps {
  service: Prestation;
  seats: number | null;
  change?: ChangementLecture;
}

/** One service: name, dated price and availability, seats left. */
export function ProposalService({ service, seats, change }: ProposalServiceProps) {
  return (
    <li className="rounded-2xl border border-line bg-card p-5">
      <h4 className="font-display text-lg font-extrabold tracking-tight text-ink">{service.nom}</h4>
      <PriceVerification service={service} change={change} seats={seats} />
    </li>
  );
}
