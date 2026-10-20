import type { ReactNode } from "react";

interface Column<T> {
  key: string;
  label: string;
  render?: (row: T) => ReactNode;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  rows: T[];
  emptyLabel?: string;
}

export function DataTable<T extends object>({
  columns,
  rows,
  emptyLabel = "Aucune donnée",
}: DataTableProps<T>) {
  if (!rows.length) {
    return (
      <div className="rounded-xl border border-border bg-surface p-8 text-center text-muted">
        {emptyLabel}
      </div>
    );
  }
  return (
    <div className="overflow-x-auto rounded-xl border border-border">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border bg-surface/50 text-left text-xs tracking-wider text-muted uppercase">
            {columns.map((col) => (
              <th key={col.key} className="px-4 py-3 font-semibold">
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className="border-b border-border/50 last:border-0 hover:bg-surface/30">
              {columns.map((col) => (
                <td key={col.key} className="px-4 py-3 text-text">
                  {col.render
                    ? col.render(row)
                    : String((row as Record<string, unknown>)[col.key] ?? "—")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
