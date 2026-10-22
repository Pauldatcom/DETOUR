import { useCallback, useEffect, useState } from "react";
import { api } from "../lib/api";
import { PublicNav } from "../components/landing/PublicNav";
import { Footer } from "../components/landing/Footer";
import { RequestList } from "../components/conseiller/workspace/RequestList";
import { RequestFile } from "../components/conseiller/workspace/RequestFile";
import type { Demande, Session } from "../types";

const NEVER = new Date(8640000000000000).getTime();

function byDeadline(requests: Demande[]): Demande[] {
  return [...requests].sort(
    (a, b) =>
      new Date(a.echeance_cible ?? NEVER).getTime() - new Date(b.echeance_cible ?? NEVER).getTime(),
  );
}

interface EspaceConseillerProps {
  nom?: string;
  session?: Session | null;
  onLogout: () => Promise<void>;
}

/** Advisor workspace (#111): the request list and one full request file side by side. */
export function EspaceConseiller({ nom, session, onLogout }: EspaceConseillerProps) {
  const [requests, setRequests] = useState<Demande[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const reload = useCallback(async () => {
    try {
      const data = await api.demandes();
      setRequests(byDeadline(data.demandes || []));
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Les demandes n'ont pas pu être chargées.");
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    api
      .demandes()
      .then((data) => {
        if (!cancelled) setRequests(byDeadline(data.demandes || []));
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Les demandes n'ont pas pu être chargées.");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="min-h-screen bg-chalk text-ink">
      <PublicNav session={session ?? null} onLogout={onLogout} />

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
        <header className="mb-6 flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="text-sm text-ballast">Espace conseiller</p>
            <h1 className="font-display text-3xl font-extrabold tracking-tight">
              {nom ? `Bonjour ${nom}` : "Bonjour"}
            </h1>
            <p className="mt-1 max-w-2xl text-sm text-ballast">
              Relisez chaque demande, vérifiez les prix et les places, puis envoyez la proposition
              en votre nom. Rien n'est réservé depuis cet écran.
            </p>
          </div>
          <button
            type="button"
            onClick={() => void reload()}
            className="rounded-full border border-line px-4 py-2 text-sm font-semibold text-ink transition hover:border-ink"
          >
            Actualiser la liste
          </button>
        </header>

        {error && (
          <p
            role="alert"
            className="mb-4 rounded-xl border border-brick/40 bg-card px-4 py-3 text-sm text-brick"
          >
            {error}
          </p>
        )}

        {loading ? (
          <p className="text-sm text-ballast">Chargement des demandes…</p>
        ) : requests.length === 0 ? (
          <p className="rounded-2xl border border-line bg-card p-10 text-center text-sm text-ballast">
            Aucune demande pour le moment.
          </p>
        ) : (
          <div className="grid gap-6 lg:grid-cols-[minmax(0,20rem)_minmax(0,1fr)]">
            <aside>
              <h2 className="mb-3 text-sm font-semibold">
                {requests.length} demande{requests.length > 1 ? "s" : ""}, par échéance
              </h2>
              <RequestList requests={requests} selectedId={selectedId} onSelect={setSelectedId} />
            </aside>
            <section aria-label="Dossier de la demande">
              {selectedId ? (
                <RequestFile
                  key={selectedId}
                  requestId={selectedId}
                  onChanged={() => void reload()}
                />
              ) : (
                <p className="rounded-2xl border border-dashed border-line p-10 text-center text-sm text-ballast">
                  Choisissez une demande pour ouvrir son dossier.
                </p>
              )}
            </section>
          </div>
        )}
      </main>
      <Footer />
    </div>
  );
}
