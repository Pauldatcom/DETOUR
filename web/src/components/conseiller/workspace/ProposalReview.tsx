import { useId, useState, type FormEvent } from "react";
import { api } from "../../../lib/api";
import { formatDateTime, formatEuro } from "../../../lib/format";
import { Logo } from "../../Logo";
import type { ChangementLecture, ContrainteVerifiee, Proposition, Recherche } from "../../../types";
import {
  CHOICE_LABELS,
  EDITABLE_STATUSES,
  PROPOSAL_ACTION_LABELS,
  PROPOSAL_STAGE,
  type ProposalAction,
} from "./labels";
import { ReasonForm } from "./ReasonForm";
import { ServicesTable, type ServiceRow } from "./ServicesTable";

interface ProposalReviewProps {
  proposal: Proposition;
  latestSearch: Recherche | null;
  onChanged: () => void;
}

type Choice = "keep" | "replace" | "drop";

const DONE_LABELS: Record<ProposalAction, string> = {
  accepter: "Envoyée au voyageur",
  demander_correction: "Correction demandée",
  refuser: "Refusée",
};

const CONSTRAINT_LABELS: Record<ContrainteVerifiee["statut"], string> = {
  ok: "Respectée",
  a_verifier: "À vérifier",
  non_respectee: "Non respectée",
};

const CONSTRAINT_STYLES: Record<ContrainteVerifiee["statut"], string> = {
  ok: "text-ink",
  a_verifier: "text-ballast",
  non_respectee: "font-medium text-brick",
};

function buildRows(proposal: Proposition, search: Recherche | null): ServiceRow[] {
  const seats = new Map((search?.resultats ?? []).map((r) => [r.id, r.places_restantes ?? null]));
  const changed = new Set((proposal.changements ?? []).filter((c) => !c.inchange).map((c) => c.id));
  return proposal.prestations.map((item) => {
    const verified = item.verification === "verifie";
    return {
      id: item.id,
      name: item.nom,
      type: item.type,
      unitPrice: verified ? item.prix_unitaire_eur : null,
      groupTotal: verified ? item.prix_total_eur : null,
      seatsLeft: seats.get(item.id) ?? null,
      available: verified ? item.disponible : null,
      checkedAt: item.consulte_le,
      state: !verified
        ? "unverified"
        : changed.has(item.id)
          ? "changed"
          : item.copie_depuis_v1
            ? "copied"
            : "verified",
    };
  });
}

/** One proposal: what the assistant prepared, what was checked, and what the advisor decides. */
export function ProposalReview({ proposal, latestSearch, onChanged }: ProposalReviewProps) {
  const editable = EDITABLE_STATUSES.has(proposal.statut);
  const [editing, setEditing] = useState(false);
  const [action, setAction] = useState<ProposalAction | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  // #121: the jumping-o animation fires only on the advisor's explicit
  // confirmation — never from chatbot output or any other action.
  const [confirmed, setConfirmed] = useState(false);
  const unverified = proposal.prestations.filter((p) => p.verification !== "verifie").length;
  const version = proposal.version ?? 1;

  async function decide(chosen: ProposalAction, reason: string, instructions: string) {
    setBusy(true);
    setError("");
    try {
      const route = chosen === "demander_correction" ? "correction" : chosen;
      await api.deciderProposition(proposal.id, route, reason, instructions || undefined);
      setAction(null);
      if (chosen === "accepter") setConfirmed(true);
      onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "La décision n'a pas été enregistrée.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <article className="rounded-2xl border border-line bg-card p-5">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs text-ballast">
            Proposition {proposal.id} · v{version}
            {proposal.parente_id ? ` (depuis ${proposal.parente_id})` : ""}
          </p>
          <h4 className="mt-0.5 font-display text-lg font-extrabold text-ink">{proposal.titre}</h4>
          <p className="text-sm text-ink">
            Total vérifié : {formatEuro(proposal.prix_total_eur)}
            {unverified > 0 && (
              <span className="text-brick">
                {" "}
                · {unverified} prestation{unverified > 1 ? "s" : ""} sans prix vérifié, hors total
              </span>
            )}
          </p>
        </div>
        <span className="rounded-full border border-line bg-chalk px-3 py-1 text-xs font-medium text-ink">
          {PROPOSAL_STAGE[proposal.statut] ?? proposal.statut}
        </span>
      </header>

      {editing ? (
        <EditForm
          proposal={proposal}
          onDone={() => {
            setEditing(false);
            onChanged();
          }}
          onCancel={() => setEditing(false)}
        />
      ) : (
        <div className="mt-4">
          <p className="text-xs text-ballast">Message au voyageur</p>
          <p className="mt-1 text-sm whitespace-pre-line text-ink">
            {proposal.description || "Aucun message pour l'instant."}
          </p>
          {editable && (
            <button
              type="button"
              onClick={() => setEditing(true)}
              className="mt-2 rounded-full border border-line px-3 py-1.5 text-xs font-semibold text-ink transition hover:border-ink"
            >
              Modifier le titre et le message
            </button>
          )}
        </div>
      )}

      <div className="mt-5">
        <ServicesTable
          rows={buildRows(proposal, latestSearch)}
          caption={`Prestations de la proposition ${proposal.id}`}
        />
      </div>

      {(proposal.contraintes_verifiees ?? []).length > 0 && (
        <section className="mt-5">
          <h5 className="text-sm font-semibold text-ink">Contraintes du voyageur</h5>
          <ul className="mt-2 space-y-1 text-sm">
            {proposal.contraintes_verifiees!.map((c) => (
              <li key={c.contrainte} className={CONSTRAINT_STYLES[c.statut]}>
                <span className="font-medium">{CONSTRAINT_LABELS[c.statut]}</span> · {c.detail}
              </li>
            ))}
          </ul>
        </section>
      )}

      {(proposal.changements ?? []).some((c) => !c.inchange) && (
        <section className="mt-5">
          <h5 className="text-sm font-semibold text-ink">Changements depuis la proposition</h5>
          <p className="text-xs text-ballast">
            Une nouvelle lecture du serveur diffère. Décidez pour chaque prestation.
          </p>
          <ul className="mt-2 space-y-3">
            {proposal
              .changements!.filter((c) => !c.inchange)
              .map((c) => (
                <ChangeLine
                  key={c.id}
                  proposal={proposal}
                  change={c}
                  search={latestSearch}
                  onChanged={onChanged}
                />
              ))}
          </ul>
        </section>
      )}

      <History proposal={proposal} />

      {editable && (
        <section className="mt-5 border-t border-line pt-4">
          <p className="text-sm text-ink">
            L'assistant a préparé ce brouillon. Rien n'est envoyé ni réservé tant que vous ne le
            validez pas.
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            {(Object.keys(PROPOSAL_ACTION_LABELS) as ProposalAction[]).map((key) => (
              <button
                key={key}
                type="button"
                onClick={() => setAction(key)}
                aria-pressed={action === key}
                className={
                  key === "accepter"
                    ? "rounded-full bg-ink px-4 py-2 text-sm font-semibold text-chalk transition hover:bg-ink/90"
                    : "rounded-full border border-line px-4 py-2 text-sm font-semibold text-ink transition hover:border-ink"
                }
              >
                {PROPOSAL_ACTION_LABELS[key]}
              </button>
            ))}
          </div>
          {action && (
            <ReasonForm
              key={action}
              title={
                action === "accepter"
                  ? "Vous envoyez cette proposition au voyageur, en votre nom."
                  : PROPOSAL_ACTION_LABELS[action]
              }
              confirmLabel={action === "accepter" ? "Envoyer au voyageur" : "Enregistrer"}
              reasonRequired={action !== "accepter"}
              instructionsLabel={
                action === "demander_correction" ? "Instructions de correction" : undefined
              }
              busy={busy}
              onSubmit={(reason, instructions) => void decide(action, reason, instructions)}
              onCancel={() => setAction(null)}
            />
          )}
          {error && (
            <p role="alert" className="mt-2 text-sm text-brick">
              {error}
            </p>
          )}
        </section>
      )}

      {confirmed && (
        <section
          aria-label="Confirmation de l'envoi"
          className="mt-5 flex items-center gap-4 rounded-xl border-2 border-ink bg-ink/5 p-4"
        >
          <Logo variant="encre" play width={48} />
          <p className="text-sm font-semibold text-ink">
            Proposition envoyée au voyageur, en votre nom. Rien n'est réservé pour l'instant.
          </p>
        </section>
      )}
    </article>
  );
}

function EditForm({
  proposal,
  onDone,
  onCancel,
}: {
  proposal: Proposition;
  onDone: () => void;
  onCancel: () => void;
}) {
  const id = useId();
  const [title, setTitle] = useState(proposal.titre);
  const [message, setMessage] = useState(proposal.description);
  const [conseiller, setConseiller] = useState(proposal.conseiller ?? "");
  const [removed, setRemoved] = useState<Set<string>>(new Set());
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  function toggleRemove(prestId: string) {
    setRemoved((prev) => {
      const next = new Set(prev);
      if (next.has(prestId)) next.delete(prestId);
      else next.add(prestId);
      return next;
    });
  }

  async function save(event: FormEvent) {
    event.preventDefault();
    if (!title.trim()) {
      setError("Le titre est obligatoire.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      // Prices are never edited by hand: the verified lines are sent back
      // unchanged — only the advisor can drop a line from the draft.
      await api.patchProposition(proposal.id, {
        titre: title.trim(),
        description: message.trim(),
        prestations: proposal.prestations.filter((p) => !removed.has(p.id)),
        ...(conseiller.trim() ? { conseiller: conseiller.trim() } : {}),
      });
      onDone();
    } catch (err) {
      setError(err instanceof Error ? err.message : "La modification n'a pas été enregistrée.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={save} className="mt-4 space-y-3 rounded-xl border border-line bg-chalk p-4">
      <div>
        <label htmlFor={`${id}-title`} className="block text-xs text-ballast">
          Titre
        </label>
        <input
          id={`${id}-title`}
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="mt-1 w-full rounded-lg border border-line bg-card px-3 py-2 text-sm text-ink"
        />
      </div>
      <div>
        <label htmlFor={`${id}-message`} className="block text-xs text-ballast">
          Message au voyageur
        </label>
        <textarea
          id={`${id}-message`}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          rows={4}
          className="mt-1 w-full rounded-lg border border-line bg-card px-3 py-2 text-sm text-ink"
        />
      </div>
      <div>
        <label htmlFor={`${id}-conseiller`} className="block text-xs text-ballast">
          Votre prénom (signe la proposition)
        </label>
        <input
          id={`${id}-conseiller`}
          value={conseiller}
          onChange={(e) => setConseiller(e.target.value)}
          placeholder="Camille"
          className="mt-1 w-full rounded-lg border border-line bg-card px-3 py-2 text-sm text-ink"
        />
      </div>
      {proposal.prestations.length > 0 && (
        <fieldset className="space-y-1.5">
          <legend className="text-xs text-ballast">Prestations du brouillon</legend>
          {proposal.prestations.map((p) => (
            <label key={p.id} className="flex items-center gap-2 text-sm text-ink">
              <input
                type="checkbox"
                checked={removed.has(p.id)}
                onChange={() => toggleRemove(p.id)}
                className="h-4 w-4 rounded border-line"
              />
              <span className={removed.has(p.id) ? "text-ballast line-through" : ""}>{p.nom}</span>
              {removed.has(p.id) && <span className="text-xs text-brick">· retirée</span>}
            </label>
          ))}
        </fieldset>
      )}
      <p className="text-xs text-ballast">
        Les prix viennent du serveur et ne se modifient pas ici.
      </p>
      {error && (
        <p role="alert" className="text-xs text-brick">
          {error}
        </p>
      )}
      <div className="flex flex-wrap gap-2">
        <button
          type="submit"
          disabled={busy}
          className="rounded-full bg-ink px-4 py-2 text-sm font-semibold text-chalk transition hover:bg-ink/90"
        >
          Enregistrer les modifications
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="rounded-full border border-line px-4 py-2 text-sm font-semibold text-ink transition hover:border-ink"
        >
          Annuler
        </button>
      </div>
    </form>
  );
}

function ChangeLine({
  proposal,
  change,
  search,
  onChanged,
}: {
  proposal: Proposition;
  change: ChangementLecture;
  search: Recherche | null;
  onChanged: () => void;
}) {
  const id = useId();
  const [choice, setChoice] = useState<Choice | null>(null);
  const [replacement, setReplacement] = useState("");
  const [error, setError] = useState("");
  const type = proposal.prestations.find((p) => p.id === change.id)?.type;
  const candidates = (search?.resultats ?? []).filter(
    (r) => r.id !== change.id && r.disponible && (!type || r.type === type),
  );

  async function submit(reason: string) {
    if (choice === "replace" && !replacement) {
      setError("Choisissez la prestation de remplacement.");
      return;
    }
    setError("");
    try {
      await api.decisionsPrestation(
        proposal.id,
        change.id,
        choice!,
        reason,
        choice === "replace" ? replacement : undefined,
      );
      setChoice(null);
      onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "La décision n'a pas été enregistrée.");
    }
  }

  return (
    <li className="rounded-xl border border-brick/40 bg-chalk p-3 text-sm">
      <p className="text-ink">
        <span className="font-medium">{change.nom}</span>
        {change.prix_change && (
          <>
            {" "}
            · prix {formatEuro(change.prix_avant)} →{" "}
            <span className="font-semibold text-brick">{formatEuro(change.prix_apres)}</span>
          </>
        )}
        {!change.disponible_apres && <span className="text-brick"> · indisponible</span>}
        {change.disponibilite_change && change.disponible_apres && " · de nouveau disponible"}
      </p>
      <div className="mt-2 flex flex-wrap gap-2">
        {(Object.keys(CHOICE_LABELS) as Choice[]).map((key) => (
          <button
            key={key}
            type="button"
            onClick={() => setChoice(key)}
            aria-pressed={choice === key}
            className="rounded-full border border-line px-3 py-1 text-xs font-semibold text-ink transition hover:border-ink"
          >
            {CHOICE_LABELS[key]}
          </button>
        ))}
      </div>
      {choice && (
        <ReasonForm
          key={choice}
          title={`${CHOICE_LABELS[choice]} « ${change.nom} »`}
          confirmLabel="Enregistrer la décision"
          reasonRequired
          onSubmit={(reason) => void submit(reason)}
          onCancel={() => setChoice(null)}
        >
          {choice === "replace" && (
            <div>
              <label htmlFor={`${id}-replacement`} className="block text-xs text-ballast">
                Prestation de remplacement
              </label>
              <select
                id={`${id}-replacement`}
                value={replacement}
                onChange={(e) => setReplacement(e.target.value)}
                className="mt-1 w-full rounded-lg border border-line bg-card px-3 py-2 text-sm text-ink"
              >
                <option value="">Choisir…</option>
                {candidates.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.nom} · {formatEuro(r.prix_unitaire_eur)} / pers.
                  </option>
                ))}
              </select>
              {candidates.length === 0 && (
                <p className="mt-1 text-xs text-ballast">
                  Aucune prestation disponible du même type dans la dernière recherche.
                </p>
              )}
            </div>
          )}
        </ReasonForm>
      )}
      {error && (
        <p role="alert" className="mt-2 text-xs text-brick">
          {error}
        </p>
      )}
    </li>
  );
}

function History({ proposal }: { proposal: Proposition }) {
  const status = proposal.decisions_statut ?? [];
  const lines = proposal.decisions ?? [];
  if (status.length === 0 && lines.length === 0) return null;
  return (
    <section className="mt-5">
      <h5 className="text-sm font-semibold text-ink">Décisions des conseillers</h5>
      <ul className="mt-2 space-y-1 text-xs text-ballast">
        {status.map((d, i) => (
          <li key={`s${i}`}>
            <span className="text-ink">
              {DONE_LABELS[d.action] ?? d.action} par {d.par}
            </span>{" "}
            · {formatDateTime(d.le)}
            {d.version ? ` · v${d.version}` : ""}
            {d.motif ? ` · ${d.motif}` : ""}
            {d.instructions ? ` · ${d.instructions}` : ""}
          </li>
        ))}
        {lines.map((d, i) => (
          <li key={`p${i}`}>
            <span className="text-ink">
              {CHOICE_LABELS[d.choix] ?? d.choix} {d.prestation_id} par {d.par}
            </span>{" "}
            · {formatDateTime(d.le)} · {d.motif}
          </li>
        ))}
      </ul>
    </section>
  );
}
