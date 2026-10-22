import { formatEuro } from "../../../lib/format";
import { SERVICE_TYPE_LABELS } from "./labels";
import { VerificationBadge, type VerificationState } from "./VerificationBadge";

export interface ServiceRow {
  id: string;
  name: string;
  type: string;
  unitPrice: number | null;
  groupTotal: number | null;
  seatsLeft: number | null;
  available: boolean | null;
  checkedAt: string | null;
  state: VerificationState;
}

interface ServicesTableProps {
  rows: ServiceRow[];
  caption: string;
}

function availabilityText(row: ServiceRow): string {
  if (row.available === null) return "Non vérifiée";
  return row.available ? "Disponible" : "Indisponible";
}

/** Prices, seats, schedule and verification of each service, in one table. */
export function ServicesTable({ rows, caption }: ServicesTableProps) {
  return (
    <div className="overflow-x-auto rounded-xl border border-line bg-card">
      <table className="w-full text-sm">
        <caption className="sr-only">{caption}</caption>
        <thead>
          <tr className="border-b border-line text-left text-xs text-ballast">
            <th scope="col" className="px-3 py-2 font-medium">
              Prestation
            </th>
            <th scope="col" className="px-3 py-2 font-medium">
              Prix / pers.
            </th>
            <th scope="col" className="px-3 py-2 font-medium">
              Total groupe
            </th>
            <th scope="col" className="px-3 py-2 font-medium">
              Places restantes
            </th>
            <th scope="col" className="px-3 py-2 font-medium">
              Horaire
            </th>
            <th scope="col" className="px-3 py-2 font-medium">
              Disponibilité
            </th>
            <th scope="col" className="px-3 py-2 font-medium">
              Vérification
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id} className="border-b border-line/60 align-top last:border-0">
              <td className="px-3 py-2.5">
                <span className="font-medium text-ink">{row.name}</span>
                <span className="block text-xs text-ballast">
                  {SERVICE_TYPE_LABELS[row.type] ?? row.type} · {row.id}
                </span>
              </td>
              <td className="px-3 py-2.5 whitespace-nowrap text-ink">
                {row.unitPrice === null ? "—" : formatEuro(row.unitPrice)}
              </td>
              <td className="px-3 py-2.5 whitespace-nowrap text-ink">
                {row.groupTotal === null ? "—" : formatEuro(row.groupTotal)}
              </td>
              <td className="px-3 py-2.5 text-ink">
                {row.seatsLeft === null ? "—" : row.seatsLeft}
              </td>
              <td className="px-3 py-2.5 text-xs text-ballast">Non communiqué par le serveur</td>
              <td
                className={`px-3 py-2.5 ${row.available === false ? "font-medium text-brick" : "text-ink"}`}
              >
                {availabilityText(row)}
              </td>
              <td className="px-3 py-2.5">
                <VerificationBadge state={row.state} checkedAt={row.checkedAt} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
