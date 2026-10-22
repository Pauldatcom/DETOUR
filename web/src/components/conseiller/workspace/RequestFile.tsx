import { useCallback, useEffect, useId, useState, type ReactNode } from "react";
import { api } from "../../../lib/api";
import { STATUT_LABELS, formatDateTime } from "../../../lib/format";
import type { Demande, Proposition } from "../../../types";
import {
  LEVEL_LABELS,
  QUALIFICATION_LABELS,
  TRIP_TYPE_LABELS,
  countNights,
  formatDay,
} from "./labels";
import { ProposalReview } from "./ProposalReview";
import { ReasonForm } from "./ReasonForm";
import { ServicesTable, type ServiceRow } from "./ServicesTable";

interface RequestFileProps {
  requestId: string;
  onChanged: () => void;
}

type PendingChange =
  | { kind: "status"; value: string }
  | { kind: "qualification"; value: "pret_proposition" | "incomplet" };

/** Everything the advisor needs to review one request, in one place. */
export function RequestFile({ requestId, onChanged }: RequestFileProps) {
  const [request, setRequest] = useState<Demande | null>(null);
  const [proposals, setProposals] = useState<Proposition[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [working, setWorking] = useState<"" | "search" | "draft">("");
  const [pending, setPending] = useState<PendingChange | null>(null);

  const load = useCallback(async () => {
    const [requestRes, proposalsRes] = await Promise.all([
      api.demande(requestId),
      api.propositions(),
    ]);
    return {
      request: requestRes.demande,
      proposals: (proposalsRes.propositions || []).filter((p) => p.demande_id === requestId),
    };
  }, [requestId]);

  const reload = useCallback(async () => {
    try {
      const data = await load();
      setRequest(data.request);
      setProposals(data.proposals);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Le dossier n'a pas pu être chargé.");
    }
  }, [load]);

  useEffect(() => {
    let cancelled = false;
    load()
      .then((data) => {
        if (cancelled) return;
        setRequest(data.request);
        setProposals(data.proposals);
        setError("");
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Le dossier n'a pas pu être chargé.");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [load]);

  async function refreshAll() {
    await reload();
    onChanged();
  }

  async function run(kind: "search" | "draft") {
    setWorking(kind);
    setError("");
    try {
      if (kind === "search") await api.rechercher(requestId);
      else await api.genererProposition(requestId);
      await refreshAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "L'action n'a pas abouti.");
    } finally {
      setWorking("");
    }
  }

  async function applyPending(reason: string) {
    if (!pending) return;
    setError("");
    try {
      if (pending.kind === "status") await api.changerStatut(requestId, pending.value, reason);
      else await api.changerQualification(requestId, pending.value, reason);
      setPending(null);
      await refreshAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "La décision n'a pas été enregistrée.");
    }
  }

  if (loading) return <p className="text-sm text-ballast">Chargement du dossier…</p>;
  if (!request) {
    return (
      <p role="alert" className="text-sm text-brick">
        {error || "Dossier introuvable."}
      </p>
    );
  }

  const data = request.demande;
  const searches = request.recherches ?? [];
  const latestSearch = searches.length > 0 ? searches[searches.length - 1] : null;
  const nights = countNights(data.date_depart, data.date_retour);
  const missing = request.champs_manquants ?? [];
  const searchRows: ServiceRow[] = (latestSearch?.resultats ?? []).map((r) => ({
    id: r.id,
    name: r.nom,
    type: r.type,
    unitPrice: r.prix_unitaire_eur,
    groupTotal: r.prix_total_eur,
    seatsLeft: r.places_restantes ?? null,
    available: r.disponible,
    checkedAt: latestSearch?.consulte_le ?? null,
    state: "verified",
  }));

  return (
    <div className="space-y-6">
      <header>
        <p className="text-xs text-ballast">Demande {request.id}</p>
        <h2 className="font-display text-2xl font-extrabold tracking-tight text-ink">
          {data.destination}, {formatDay(data.date_depart)}
        </h2>
        <div className="mt-2 flex flex-wrap gap-2 text-xs">
          <Chip>Statut : {STATUT_LABELS[request.statut] ?? request.statut}</Chip>
          <Chip>
            Qualification :{" "}
            {QUALIFICATION_LABELS[request.qualification ?? ""] ?? request.qualification ?? "—"}
          </Chip>
          {request.echeance_cible && (
            <Chip tone={request.echeance_statut === "ok" ? "default" : "alert"}>
              Réponse attendue avant le {formatDateTime(request.echeance_cible)}
              {request.echeance_statut === "depassee" ? " · échéance dépassée" : ""}
            </Chip>
          )}
        </div>
      </header>

      <p className="rounded-xl border border-sky bg-sky/30 px-4 py-3 text-sm text-ink">
        Vous êtes responsable de ce dossier. L'assistant recueille la demande et prépare des
        brouillons ; il ne réserve rien et n'envoie rien. Chaque envoi au voyageur se fait en votre
        nom.
      </p>

      {error && (
        <p
          role="alert"
          className="rounded-xl border border-brick/40 bg-card px-4 py-3 text-sm text-brick"
        >
          {error}
        </p>
      )}

      <section aria-labelledby={`${requestId}-traveler`} className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-2xl border border-line bg-card p-5">
          <h3 id={`${requestId}-traveler`} className="text-sm font-semibold text-ink">
            Voyageur
          </h3>
          <dl className="mt-3 grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
            <Field label="Nom" value={request.client?.nom ?? "Non renseigné"} />
            <Field label="E-mail" value={request.client?.email ?? "Non renseigné"} />
            <Field
              label="Voyageurs"
              value={`${data.nombre_voyageurs} personne${data.nombre_voyageurs > 1 ? "s" : ""}${
                data.has_enfants ? `, dont ${data.nombre_enfants} enfant(s)` : ""
              }`}
            />
            <Field label="Budget max." value={`${data.budget_max_par_personne} € par personne`} />
            <Field
              label="Niveau"
              value={LEVEL_LABELS[data.niveau_aventure] ?? data.niveau_aventure}
            />
            <Field label="Guide" value={data.besoin_guide ? "Souhaité" : "Non souhaité"} />
            <Field
              label="Activités"
              value={data.activites.length ? data.activites.join(", ") : "Aucune précisée"}
            />
            <Field label="Allergies, contraintes" value={data.contraintes || "Aucune signalée"} />
            <div className="col-span-2">
              <Field label="Souhaits" value={data.souhaits || "Aucun précisé"} />
            </div>
          </dl>
          {missing.length > 0 && (
            <p className="mt-3 text-sm text-brick">
              Informations obligatoires manquantes : {missing.join(", ")}
            </p>
          )}
        </div>

        <div className="rounded-2xl border border-line bg-card p-5">
          <h3 className="text-sm font-semibold text-ink">Voyage</h3>
          <dl className="mt-3 grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
            <Field label="Destination" value={data.destination} />
            <Field label="Type" value={TRIP_TYPE_LABELS[data.type_voyage] ?? data.type_voyage} />
            <Field label="Départ" value={formatDay(data.date_depart)} />
            <Field label="Retour" value={formatDay(data.date_retour)} />
            <Field
              label="Durée"
              value={nights === null ? "—" : `${nights} nuit${nights > 1 ? "s" : ""}`}
            />
            <Field label="Demande reçue" value={formatDateTime(request.cree_le)} />
          </dl>
          <RequestDecisions
            request={request}
            pending={pending}
            onPick={setPending}
            onCancel={() => setPending(null)}
            onConfirm={(reason) => void applyPending(reason)}
          />
        </div>
      </section>

      <section className="space-y-3">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h3 className="text-sm font-semibold text-ink">Prestations vérifiées</h3>
            <p className="text-xs text-ballast">
              {latestSearch
                ? `Lecture du serveur du ${formatDateTime(latestSearch.consulte_le)} · disponibilité vérifiée à la date de départ.`
                : "Aucune lecture du serveur pour cette demande."}
            </p>
          </div>
          <button
            type="button"
            onClick={() => void run("search")}
            disabled={working !== ""}
            className="rounded-full border border-line px-4 py-2 text-sm font-semibold text-ink transition hover:border-ink"
          >
            {working === "search" ? "Lecture en cours…" : "Relire les prix et les places"}
          </button>
        </div>
        {searchRows.length > 0 && (
          <ServicesTable rows={searchRows} caption="Dernière lecture du serveur" />
        )}
      </section>

      <section className="space-y-3">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <h3 className="text-sm font-semibold text-ink">Propositions</h3>
          <button
            type="button"
            onClick={() => void run("draft")}
            disabled={working !== ""}
            className="rounded-full border border-ink px-4 py-2 text-sm font-semibold text-ink transition hover:bg-ink hover:text-chalk"
          >
            {working === "draft" ? "Préparation…" : "Préparer un brouillon avec l'assistant"}
          </button>
        </div>
        {proposals.length === 0 ? (
          <p className="text-sm text-ballast">Aucune proposition pour cette demande.</p>
        ) : (
          proposals.map((p) => (
            <ProposalReview
              key={p.id}
              proposal={p}
              latestSearch={latestSearch}
              onChanged={() => void refreshAll()}
            />
          ))
        )}
      </section>
    </div>
  );
}

function RequestDecisions({
  request,
  pending,
  onPick,
  onCancel,
  onConfirm,
}: {
  request: Demande;
  pending: PendingChange | null;
  onPick: (change: PendingChange) => void;
  onCancel: () => void;
  onConfirm: (reason: string) => void;
}) {
  const id = useId();
  const title =
    pending?.kind === "status"
      ? `Passer la demande en « ${STATUT_LABELS[pending.value] ?? pending.value} »`
      : pending?.value === "pret_proposition"
        ? "Valider la demande pour proposition"
        : "Renvoyer la demande en incomplet";
  return (
    <div className="mt-5 border-t border-line pt-4">
      <div className="flex flex-wrap items-end gap-2">
        <button
          type="button"
          onClick={() => onPick({ kind: "qualification", value: "pret_proposition" })}
          disabled={request.qualification === "pret_proposition"}
          className="rounded-full border border-line px-3 py-1.5 text-xs font-semibold text-ink transition hover:border-ink"
        >
          Valider pour proposition
        </button>
        <button
          type="button"
          onClick={() => onPick({ kind: "qualification", value: "incomplet" })}
          disabled={request.qualification === "incomplet"}
          className="rounded-full border border-line px-3 py-1.5 text-xs font-semibold text-ink transition hover:border-ink"
        >
          Renvoyer en incomplet
        </button>
        <div>
          <label htmlFor={`${id}-status`} className="block text-xs text-ballast">
            Statut
          </label>
          <select
            id={`${id}-status`}
            value={pending?.kind === "status" ? pending.value : request.statut}
            onChange={(e) => {
              if (e.target.value !== request.statut) {
                onPick({ kind: "status", value: e.target.value });
              }
            }}
            className="mt-1 rounded-lg border border-line bg-card px-2 py-1.5 text-xs text-ink"
          >
            {Object.entries(STATUT_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>
      </div>
      {pending && (
        <ReasonForm
          key={`${pending.kind}-${pending.value}`}
          title={title}
          confirmLabel="Enregistrer"
          reasonRequired
          onSubmit={(reason) => onConfirm(reason)}
          onCancel={onCancel}
        />
      )}
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs text-ballast">{label}</dt>
      <dd className="mt-0.5 text-ink">{value}</dd>
    </div>
  );
}

function Chip({ children, tone = "default" }: { children: ReactNode; tone?: "default" | "alert" }) {
  return (
    <span
      className={`rounded-full border px-2.5 py-1 ${
        tone === "alert" ? "border-brick text-brick" : "border-line bg-card text-ink"
      }`}
    >
      {children}
    </span>
  );
}
