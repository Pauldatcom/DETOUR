import { useCallback, useEffect, useState } from "react";
import { api } from "../lib/api";
import { PublicNav } from "../components/landing/PublicNav";
import { Footer } from "../components/landing/Footer";
import type { Session } from "../types";
import type {
  Demande,
  Proposition,
  ChangementLecture,
  ContrainteVerifiee,
  Prestation,
} from "../types";
import {
  STATUT_LABELS,
  PROP_STATUT_LABELS,
  STATUT_COLORS,
  formatEuro,
  formatDateTime,
} from "../lib/format";

const QUALIFICATION_LABELS: Record<string, string> = {
  incomplet: "Incomplète",
  en_cours: "En cours",
  pret_relecture: "Prête pour relecture",
  pret_proposition: "Prête pour proposition",
};

const TYPE_LABELS: Record<string, string> = {
  "trek-randonnee": "Trek / Randonnée",
  "lune-de-miel": "Lune de miel",
  "voyage-familial": "Voyage familial",
  autres: "Autres",
};

const NIVEAU_LABELS: Record<string, string> = {
  calme: "Calme",
  modere: "Modéré",
  intense: "Intense",
};

const DECISION_LABELS: Record<string, string> = {
  keep: "Garder",
  replace: "Remplacer",
  drop: "Retirer",
};

const DECISION_PROPOSITION = [
  { action: "accepter" as const, label: "Accepter", motif: false },
  { action: "demander_correction" as const, label: "Demander une correction", motif: true },
  { action: "refuser" as const, label: "Refuser", motif: true },
];

const JAMMAIS = new Date(8640000000000000).getTime();

function demanderMotif(question: string): string | null {
  const reponse = window.prompt(`${question}\nMotif (obligatoire) :`);
  if (reponse === null) return null;
  const motif = reponse.trim();
  if (!motif) {
    window.alert("Le motif de la décision est obligatoire.");
    return demanderMotif(question);
  }
  return motif;
}

interface EspaceConseillerProps {
  nom?: string;
  session?: Session | null;
  onLogout: () => Promise<void>;
}

export function EspaceConseiller({ nom, session, onLogout }: EspaceConseillerProps) {
  const [demandes, setDemandes] = useState<Demande[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const charger = useCallback(async () => {
    setError("");
    try {
      const data = await api.demandes();
      const sorted = (data.demandes || []).sort(
        (a, b) =>
          new Date(a.echeance_cible ?? JAMMAIS).getTime() -
          new Date(b.echeance_cible ?? JAMMAIS).getTime(),
      );
      setDemandes(sorted);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    api
      .demandes()
      .then((data) => {
        if (cancelled) return;
        setDemandes(
          (data.demandes || []).sort(
            (a, b) =>
              new Date(a.echeance_cible ?? JAMMAIS).getTime() -
              new Date(b.echeance_cible ?? JAMMAIS).getTime(),
          ),
        );
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Erreur");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const selected = selectedId ? (demandes.find((d) => d.id === selectedId) ?? null) : null;

  return (
    <div className="min-h-screen bg-[#f7fafd] text-[#0b2447]">
      <PublicNav session={session ?? null} onLogout={onLogout} />

      {/* Hero */}
      <section className="bg-[#0b2447] py-10 text-white lg:py-14">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <p className="mb-1 text-xs font-semibold tracking-widest text-[#7fd9d5] uppercase">
            Espace conseiller
          </p>
          <h1 className="text-2xl font-bold sm:text-3xl">Tableau de bord</h1>
          <p className="mt-2 max-w-2xl text-sm text-[#c9d9ec]">
            {nom ? `Bonjour ${nom}, ` : "Bonjour, "}
            toutes les demandes des voyageurs, avec les résultats vérifiés auprès du serveur fictif.
            Suivez leur avancement, validez ou refusez chaque demande.
          </p>
        </div>
      </section>

      {/* Demandes */}
      <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold tracking-widest text-[#38bdb8] uppercase">
              01 / Suivi
            </p>
            <h2 className="mt-0.5 text-xl font-bold">Demandes des voyageurs</h2>
          </div>
          <button
            onClick={() => void charger()}
            className="rounded-full border border-[#d5e0ee] px-4 py-2 text-sm font-semibold text-[#0b2447] transition outline-none hover:border-[#38bdb8] focus-visible:ring-2 focus-visible:ring-[#38bdb8]"
          >
            Actualiser ↻
          </button>
        </div>

        {error && (
          <div className="mb-4 rounded-xl border border-[#fce8e8] bg-[#fff0f0] px-4 py-3 text-sm text-[#b91c1c]">
            {error}
          </div>
        )}

        {loading && <p className="text-sm text-[#4b6480]">Chargement…</p>}

        {!loading && demandes.length === 0 && (
          <div className="rounded-2xl border border-[#e8eef6] bg-white p-12 text-center">
            <p className="text-sm text-[#4b6480]">Aucune demande pour le moment.</p>
          </div>
        )}

        {!loading && demandes.length > 0 && (
          <div className="overflow-x-auto rounded-2xl border border-[#e8eef6] bg-white shadow-sm">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[#e8eef6] bg-[#f7fafd] text-left text-xs tracking-wider text-[#4b6480] uppercase">
                  <th className="px-3 py-3 font-semibold">Demande</th>
                  <th className="px-3 py-3 font-semibold">Voyageur</th>
                  <th className="px-3 py-3 font-semibold">Voyage</th>
                  <th className="px-3 py-3 font-semibold">Dates</th>
                  <th className="px-3 py-3 font-semibold">Budget</th>
                  <th className="px-3 py-3 font-semibold">Créée le</th>
                  <th className="px-3 py-3 font-semibold">Échéance</th>
                  <th className="px-3 py-3 font-semibold">Qualification</th>
                  <th className="px-3 py-3 font-semibold">Statut</th>
                  <th className="px-3 py-3"></th>
                </tr>
              </thead>
              <tbody>
                {demandes.map((d) => (
                  <DemandeRow
                    key={d.id}
                    demande={d}
                    isSelected={selectedId === d.id}
                    onSelect={() => setSelectedId(d.id)}
                    onChanged={() => void charger()}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Detail */}
        {selected && (
          <DemandeDetail
            demandeId={selected.id}
            onClose={() => setSelectedId(null)}
            onChanged={() => void charger()}
          />
        )}
      </main>
      <Footer />
    </div>
  );
}

/* ── Row ────────────────────────────────────────────────────────── */

interface DemandeRowProps {
  demande: Demande;
  isSelected: boolean;
  onSelect: () => void;
  onChanged: () => void;
}

function DemandeRow({ demande: d, isSelected, onSelect, onChanged }: DemandeRowProps) {
  const data = d.demande;
  const client = d.client;

  async function handleStatut(nouveau: string) {
    if (nouveau === d.statut) return;
    const motif = demanderMotif(`Passer la demande en « ${STATUT_LABELS[nouveau] ?? nouveau} »`);
    if (motif === null) return;
    try {
      await api.changerStatut(d.id, nouveau, motif);
      onChanged();
    } catch (err) {
      window.alert(err instanceof Error ? err.message : "Erreur");
    }
  }

  async function handleQualification(qualification: string) {
    const motif = demanderMotif(
      qualification === "pret_proposition"
        ? "Valider la demande pour proposition"
        : "Renvoyer la demande en incomplet",
    );
    if (motif === null) return;
    try {
      await api.changerQualification(d.id, qualification, motif);
      onChanged();
    } catch (err) {
      window.alert(err instanceof Error ? err.message : "Erreur");
    }
  }

  const echeanceClass =
    d.echeance_statut === "depassee"
      ? "text-[#b91c1c]"
      : d.echeance_statut === "approche"
        ? "text-[#c98a00]"
        : "text-[#4b6480]";

  return (
    <tr
      className={`border-b border-[#e8eef6]/50 last:border-0 hover:bg-[#f7fafd]/50 ${
        isSelected ? "bg-[#f0eefe]/30" : ""
      }`}
    >
      <td className="px-3 py-3 font-mono text-xs text-[#4b6480]">{d.id}</td>
      <td className="px-3 py-3 text-sm text-[#0b2447]">
        {client ? (
          <span>
            <span className="font-medium">{client.nom}</span>
            <span className="block text-xs text-[#8ba8c4]">{client.email}</span>
          </span>
        ) : (
          "—"
        )}
      </td>
      <td className="px-3 py-3 text-sm text-[#4b6480]">
        <span className="font-medium text-[#0b2447]">{data.destination}</span>
        <span className="block text-xs text-[#8ba8c4]">
          {TYPE_LABELS[data.type_voyage] ?? data.type_voyage} · {data.nombre_voyageurs} voyageur(s)
        </span>
      </td>
      <td className="px-3 py-3 text-xs text-[#4b6480]">
        {data.date_depart} → {data.date_retour}
      </td>
      <td className="px-3 py-3 text-xs text-[#4b6480]">{data.budget_max_par_personne} €/pers.</td>
      <td className="px-3 py-3 text-xs text-[#4b6480]">{formatDateTime(d.cree_le)}</td>
      <td className={`px-3 py-3 text-xs ${echeanceClass}`}>
        {d.echeance_cible ? formatDateTime(d.echeance_cible) : "—"}
      </td>
      <td className="px-3 py-3">
        <div className="flex flex-col gap-1">
          <span className="text-xs font-medium text-[#0b2447]">
            {QUALIFICATION_LABELS[d.qualification ?? ""] ?? d.qualification ?? "—"}
          </span>
          <div className="flex gap-1">
            <button
              onClick={() => void handleQualification("incomplet")}
              disabled={d.qualification === "incomplet"}
              className="rounded border border-[#d5e0ee] px-2 py-0.5 text-[10px] font-medium text-[#4b6480] transition hover:border-[#38bdb8] disabled:opacity-40"
            >
              Incomplet
            </button>
            <button
              onClick={() => void handleQualification("pret_proposition")}
              disabled={d.qualification === "pret_proposition"}
              title={
                (d.champs_manquants ?? []).length
                  ? "Champs manquants : " + (d.champs_manquants ?? []).join(", ")
                  : ""
              }
              className="rounded border border-[#d5e0ee] px-2 py-0.5 text-[10px] font-medium text-[#0b2447] transition hover:border-[#38bdb8] disabled:opacity-40"
            >
              Valider
            </button>
          </div>
        </div>
      </td>
      <td className="px-3 py-3">
        <select
          value={d.statut}
          onChange={(e) => void handleStatut(e.target.value)}
          className="rounded-lg border border-[#d5e0ee] bg-[#f7fafd] px-2 py-1 text-xs font-medium text-[#0b2447] outline-none focus:border-[#38bdb8]"
          aria-label="Statut de la demande"
        >
          {Object.entries(STATUT_LABELS).map(([valeur, label]) => (
            <option key={valeur} value={valeur}>
              {label}
            </option>
          ))}
        </select>
      </td>
      <td className="px-3 py-3">
        <button
          onClick={onSelect}
          className="rounded-full border border-[#d5e0ee] px-3 py-1 text-xs font-semibold text-[#0b2447] transition hover:border-[#38bdb8] focus-visible:ring-2 focus-visible:ring-[#38bdb8]"
        >
          Détail
        </button>
      </td>
    </tr>
  );
}

/* ── Detail ─────────────────────────────────────────────────────── */

interface DemandeDetailProps {
  demandeId: string;
  onClose: () => void;
  onChanged: () => void;
}

function DemandeDetail({ demandeId, onClose, onChanged }: DemandeDetailProps) {
  const [demande, setDemande] = useState<Demande | null>(null);
  const [propositions, setPropositions] = useState<Proposition[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [generating, setGenerating] = useState(false);

  const charger = useCallback(async () => {
    setError("");
    try {
      const [demRes, propsRes] = await Promise.all([api.demande(demandeId), api.propositions()]);
      setDemande(demRes.demande);
      setPropositions((propsRes.propositions || []).filter((p) => p.demande_id === demandeId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur");
    } finally {
      setLoading(false);
    }
  }, [demandeId]);

  useEffect(() => {
    let cancelled = false;
    Promise.all([api.demande(demandeId), api.propositions()])
      .then(([demRes, propsRes]) => {
        if (cancelled) return;
        setDemande(demRes.demande);
        setPropositions((propsRes.propositions || []).filter((p) => p.demande_id === demandeId));
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Erreur");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [demandeId]);

  async function handleGenerer() {
    setGenerating(true);
    setError("");
    try {
      await api.genererProposition(demandeId);
      await charger();
      onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur génération");
    } finally {
      setGenerating(false);
    }
  }

  async function handleRelancerRecherche() {
    setError("");
    try {
      await api.rechercher(demandeId);
      await charger();
      onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur recherche");
    }
  }

  if (loading) return <p className="mt-6 text-sm text-[#4b6480]">Chargement du détail…</p>;
  if (error) return <p className="mt-6 text-sm text-[#b91c1c]">{error}</p>;
  if (!demande) return null;

  const d = demande.demande;
  const recherches = demande.recherches ?? [];
  const derniereRecherche = recherches.length > 0 ? recherches[recherches.length - 1] : null;

  return (
    <section className="mt-8 rounded-2xl border border-[#e8eef6] bg-white p-6 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold tracking-widest text-[#38bdb8] uppercase">
            02 / Détail
          </p>
          <h2 className="mt-0.5 text-lg font-bold">Demande {demande.id}</h2>
          <p className="mt-1 text-sm text-[#4b6480]">
            Qualification :{" "}
            {QUALIFICATION_LABELS[demande.qualification ?? ""] ?? demande.qualification ?? "—"} —
            Statut : {STATUT_LABELS[demande.statut] ?? demande.statut}
          </p>
          {demande.client && (
            <p className="text-sm text-[#4b6480]">
              Voyageur : {demande.client.nom} ({demande.client.email})
            </p>
          )}
          {(demande.champs_manquants ?? []).length > 0 && (
            <p className="mt-1 text-xs text-[#b91c1c]">
              Informations obligatoires manquantes : {demande.champs_manquants!.join(", ")}
            </p>
          )}
        </div>
        <button
          onClick={onClose}
          className="rounded-full border border-[#d5e0ee] px-4 py-2 text-sm font-semibold text-[#0b2447] transition hover:border-[#38bdb8] focus-visible:ring-2 focus-visible:ring-[#38bdb8]"
        >
          Fermer
        </button>
      </div>

      {/* Champs demande */}
      <div className="grid gap-3 rounded-xl border border-[#e8eef6] bg-[#f7fafd] p-4 sm:grid-cols-2 lg:grid-cols-3">
        <Champ label="Type de voyage" valeur={TYPE_LABELS[d.type_voyage] ?? d.type_voyage} />
        <Champ label="Destination" valeur={d.destination} />
        <Champ label="Dates" valeur={`${d.date_depart} → ${d.date_retour}`} />
        <Champ label="Voyageurs" valeur={String(d.nombre_voyageurs)} />
        <Champ label="Enfants" valeur={d.has_enfants ? `${d.nombre_enfants} enfant(s)` : "Non"} />
        <Champ label="Budget max / pers." valeur={`${d.budget_max_par_personne} €`} />
        <Champ
          label="Niveau d'aventure"
          valeur={NIVEAU_LABELS[d.niveau_aventure] ?? d.niveau_aventure}
        />
        <Champ label="Guide requis" valeur={d.besoin_guide ? "Oui" : "Non"} />
        <Champ label="Activités" valeur={d.activites.length ? d.activites.join(", ") : "—"} />
        <Champ label="Allergies / contraintes" valeur={d.contraintes || "—"} />
        <div className="sm:col-span-2 lg:col-span-3">
          <Champ label="Souhaits / ambiance" valeur={d.souhaits || "—"} />
        </div>
      </div>

      {/* Recherche */}
      <div className="mt-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold">Dernières prestations vérifiées</h3>
          <button
            onClick={() => void handleRelancerRecherche()}
            className="rounded-full border border-[#d5e0ee] px-3 py-1 text-xs font-semibold text-[#0b2447] transition hover:border-[#38bdb8]"
          >
            Relancer la recherche
          </button>
        </div>
        {derniereRecherche ? (
          <div className="mt-2">
            <p className="text-xs text-[#8ba8c4]">
              Source : {derniereRecherche.source_label} — vérifié le{" "}
              {formatDateTime(derniereRecherche.consulte_le)}
            </p>
            <ul className="mt-2 space-y-1 text-sm text-[#4b6480]">
              {derniereRecherche.resultats.map((item) => (
                <li key={item.id}>
                  <span className="font-medium text-[#0b2447]">{item.nom}</span> ({item.id}) —{" "}
                  {item.prix_unitaire_eur} €/pers · {item.prix_total_eur} € pour le groupe ·{" "}
                  {item.disponible ? "disponible" : "indisponible"}
                </li>
              ))}
            </ul>
          </div>
        ) : (
          <p className="mt-2 text-sm text-[#4b6480]">
            Aucune recherche vérifiée pour cette demande.
          </p>
        )}
      </div>

      {/* Propositions */}
      <div className="mt-6">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold">Propositions</h3>
          <button
            onClick={() => void handleGenerer()}
            disabled={generating}
            className="rounded-full bg-[#0b2447] px-4 py-2 text-xs font-semibold text-white transition hover:bg-[#12335e] disabled:opacity-60"
          >
            {generating ? "Génération…" : "Générer une proposition (IA)"}
          </button>
        </div>

        {propositions.length === 0 ? (
          <p className="mt-2 text-sm text-[#4b6480]">Aucune proposition pour cette demande.</p>
        ) : (
          <div className="mt-3 space-y-4">
            {propositions.map((prop) => (
              <PropositionBloc
                key={prop.id}
                proposition={prop}
                onChanged={() => {
                  void charger();
                  onChanged();
                }}
              />
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

function Champ({ label, valeur }: { label: string; valeur: string }) {
  return (
    <div>
      <div className="text-xs font-medium tracking-wide text-[#8ba8c4] uppercase">{label}</div>
      <div className="mt-0.5 text-sm text-[#0b2447]">{valeur}</div>
    </div>
  );
}

/* ── Proposition bloc ───────────────────────────────────────────── */

interface PropositionBlocProps {
  proposition: Proposition;
  onChanged: () => void;
}

function PropositionBloc({ proposition: prop, onChanged }: PropositionBlocProps) {
  const [motifVisible, setMotifVisible] = useState(false);
  const [motif, setMotif] = useState("");
  const [instructions, setInstructions] = useState("");
  const [decisionActive, setDecisionActive] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function envoyer(action: "accepter" | "demander_correction" | "refuser") {
    setError("");
    if (decisionActive !== action) {
      setDecisionActive(action);
      setMotifVisible(true);
      return;
    }
    const m = motif.trim();
    if (!m && action !== "accepter") {
      window.alert("Le motif est obligatoire.");
      return;
    }
    setBusy(true);
    try {
      const route = action === "demander_correction" ? "correction" : action;
      await api.deciderProposition(prop.id, route, m, instructions.trim() || undefined);
      setMotifVisible(false);
      setDecisionActive(null);
      setMotif("");
      setInstructions("");
      onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur");
    } finally {
      setBusy(false);
    }
  }

  async function decisionPrestation(
    changement: ChangementLecture,
    choix: "keep" | "replace" | "drop",
  ) {
    const m = window.prompt("Motif (obligatoire) :");
    if (!m?.trim()) return;
    let remplacementId: string | undefined;
    if (choix === "replace") {
      remplacementId = window.prompt("Id de la prestation de remplacement :") ?? undefined;
      if (!remplacementId) return;
    }
    try {
      await api.decisionsPrestation(prop.id, changement.id, choix, m.trim(), remplacementId);
      onChanged();
    } catch (err) {
      window.alert(err instanceof Error ? err.message : "Erreur");
    }
  }

  const version = prop.version ?? 1;
  const versionLabel = prop.parente_id
    ? ` · v${version} (depuis ${prop.parente_id})`
    : ` · v${version}`;

  return (
    <div className="rounded-xl border border-[#e8eef6] bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-bold text-[#0b2447]">
            {prop.titre} ({prop.id}){versionLabel}
          </p>
          <p className="text-xs text-[#8ba8c4]">Total : {formatEuro(prop.prix_total_eur)}</p>
        </div>
        <span
          className={`inline-flex items-center rounded-full border border-[#e8eef6] px-2.5 py-0.5 text-xs font-semibold ${STATUT_COLORS[prop.statut] ?? "text-[#8ba8c4]"}`}
        >
          {PROP_STATUT_LABELS[prop.statut] ?? prop.statut}
        </span>
      </div>

      {/* Décisions conseiller sur la proposition */}
      <div className="mt-3 flex flex-wrap gap-2">
        {DECISION_PROPOSITION.map((dec) => (
          <button
            key={dec.action}
            onClick={() => void envoyer(dec.action)}
            disabled={busy}
            className="rounded-full border border-[#d5e0ee] px-3 py-1.5 text-xs font-semibold text-[#0b2447] transition hover:border-[#38bdb8] disabled:opacity-60"
          >
            {dec.label}
          </button>
        ))}
      </div>

      {motifVisible && decisionActive && (
        <div className="mt-2 space-y-2 rounded-lg border border-[#e8eef6] bg-[#f7fafd] p-3">
          <textarea
            value={motif}
            onChange={(e) => setMotif(e.target.value)}
            rows={2}
            placeholder="Motif (obligatoire)"
            className="w-full rounded-lg border border-[#d5e0ee] bg-white px-3 py-2 text-sm outline-none focus:border-[#38bdb8]"
          />
          {decisionActive === "demander_correction" && (
            <textarea
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
              rows={2}
              placeholder="Instructions de correction (obligatoire)"
              className="w-full rounded-lg border border-[#d5e0ee] bg-white px-3 py-2 text-sm outline-none focus:border-[#38bdb8]"
            />
          )}
        </div>
      )}

      {error && <p className="mt-2 text-xs text-[#b91c1c]">{error}</p>}

      {/* Prestations */}
      {prop.prestations.length > 0 && (
        <ul className="mt-3 space-y-1 border-t border-[#e8eef6] pt-3">
          {prop.prestations.map((item: Prestation) => (
            <PrestationLine key={item.id} item={item} />
          ))}
        </ul>
      )}

      {/* Contraintes vérifiées */}
      {prop.contraintes_verifiees && prop.contraintes_verifiees.length > 0 && (
        <div className="mt-3">
          <p className="text-xs font-semibold text-[#0b2447]">Contraintes prises en compte :</p>
          <ul className="mt-1 space-y-0.5 text-xs text-[#4b6480]">
            {prop.contraintes_verifiees.map((c: ContrainteVerifiee) => (
              <li key={c.contrainte}>
                {c.statut === "ok" ? "✅" : c.statut === "non_respectee" ? "❌" : "⚠️"} {c.detail}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Changements de lecture */}
      {prop.changements && prop.changements.length > 0 && (
        <div className="mt-3">
          <p className="text-xs font-semibold text-[#0b2447]">Nouvelle lecture :</p>
          <ul className="mt-1 space-y-1 text-xs text-[#4b6480]">
            {prop.changements.map((c) => (
              <li key={c.id}>
                {c.inchange ? (
                  `${c.nom} (${c.id}) — prix et disponibilité inchangés (${c.prix_apres} €/pers)`
                ) : (
                  <>
                    <span className="font-medium">{c.nom}</span> ({c.id}) —{" "}
                    {c.prix_change && (
                      <>
                        prix {c.prix_avant} € → {c.prix_apres} €
                      </>
                    )}
                    {c.disponibilite_change && (
                      <>{c.disponible_apres ? " · devenu disponible" : " · indisponible"}</>
                    )}
                    {!c.disponible_apres && !c.disponibilite_change && " · indisponible"}
                    <div className="mt-1 flex gap-1">
                      {Object.entries(DECISION_LABELS).map(([choix, label]) => (
                        <button
                          key={choix}
                          onClick={() =>
                            void decisionPrestation(c, choix as "keep" | "replace" | "drop")
                          }
                          className="rounded border border-[#d5e0ee] px-2 py-0.5 text-[10px] font-medium text-[#4b6480] transition hover:border-[#38bdb8]"
                        >
                          {label}
                        </button>
                      ))}
                    </div>
                  </>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Décisions prestations */}
      {prop.decisions && prop.decisions.length > 0 && (
        <div className="mt-3">
          <p className="text-xs font-semibold text-[#0b2447]">Décisions conseiller :</p>
          <ul className="mt-1 space-y-0.5 text-xs text-[#4b6480]">
            {prop.decisions.map((dec, i) => (
              <li key={i}>
                {dec.prestation_id} — {DECISION_LABELS[dec.choix] ?? dec.choix} · {dec.par} ·{" "}
                {formatDateTime(dec.le)} · {dec.motif}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Historique décisions statut */}
      {prop.decisions_statut && prop.decisions_statut.length > 0 && (
        <div className="mt-3">
          <p className="text-xs font-semibold text-[#0b2447]">Décisions sur la proposition :</p>
          <ul className="mt-1 space-y-0.5 text-xs text-[#4b6480]">
            {prop.decisions_statut.map((dec, i) => {
              const actionLabel =
                DECISION_PROPOSITION.find((x) => x.action === dec.action)?.label ?? dec.action;
              const parties = [actionLabel];
              if (dec.motif) parties.push(dec.motif);
              if (dec.instructions) parties.push(dec.instructions);
              return (
                <li key={i}>
                  {parties.join(" — ")} · {dec.par} · {formatDateTime(dec.le)}
                  {dec.version ? ` · v${dec.version}` : ""}
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}

function PrestationLine({ item }: { item: Prestation }) {
  if (item.verification !== "verifie") {
    return (
      <li className="text-sm text-[#4b6480]">
        <span className="font-medium text-[#0b2447]">{item.nom}</span>
        <span className="text-[#8ba8c4]"> ({item.id})</span>
        <span> — manquant</span>
      </li>
    );
  }
  return (
    <li className="text-sm text-[#4b6480]">
      <span className="font-medium text-[#0b2447]">{item.nom}</span>
      <span className="text-[#8ba8c4]"> ({item.id})</span>
      <span>
        {" "}
        — {formatEuro(item.prix_unitaire_eur ?? 0)} / pers
        {item.disponible === false ? " · indisponible" : " · disponible"}
      </span>
      <div className="mt-0.5 text-xs text-[#8ba8c4]">
        {item.source} · {formatDateTime(item.consulte_le ?? "")}
      </div>
    </li>
  );
}
