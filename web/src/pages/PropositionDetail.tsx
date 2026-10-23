import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ProposalService } from "../components/traveler/ProposalService";
import { ProposalTotal } from "../components/traveler/PriceVerification";
import { api } from "../lib/api";
import { advisorFirstName, formatLongDay, nightsBetween } from "../lib/tone";
import type { Demande, Prestation, Proposition } from "../types";

const SECTIONS: { type: string; title: string }[] = [
  { type: "transport", title: "Le trajet" },
  { type: "hebergement", title: "Où vous dormez" },
  { type: "activite", title: "Ce que vous faites" },
];

const STATUS_SENTENCE: Record<string, string> = {
  envoyee: "Rien n'est réservé pour l'instant : votre conseiller attend votre retour.",
  validee: "Proposition validée. Rien n'est encore réservé.",
  refusee: "Cette proposition n'est plus d'actualité.",
};

function plural(count: number, word: string): string {
  return `${count} ${word}${count > 1 ? "s" : ""}`;
}

function tripSummary(request: Demande | null): string {
  if (!request) return "";
  const d = request.demande;
  const nights = nightsBetween(d.date_depart, d.date_retour);
  const parts = [
    `Du ${formatLongDay(d.date_depart)} au ${formatLongDay(d.date_retour)}`,
    nights !== null ? plural(nights, "nuit") : "",
    plural(d.nombre_voyageurs, "voyageur"),
  ];
  return parts.filter(Boolean).join(" · ");
}

/** Traveler proposal page (#112): the full itinerary, dated prices, seats, signed. */
export function PropositionDetail() {
  const { id } = useParams<{ id: string }>();
  const [proposal, setProposal] = useState<Proposition | null>(null);
  const [request, setRequest] = useState<Demande | null>(null);
  const [error, setError] = useState("");
  const [readyFor, setReadyFor] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    api
      .proposition(id)
      .then(async (data) => {
        // The request carries the trip dates and the seats left; the page still
        // shows the proposal if it cannot be read.
        const requestData = await api.demande(data.proposition.demande_id).catch(() => null);
        if (cancelled) return;
        setProposal(data.proposition);
        setRequest(requestData?.demande ?? null);
        setError("");
        setReadyFor(id);
      })
      .catch((err) => {
        if (cancelled) return;
        setProposal(null);
        setError(err instanceof Error ? err.message : "Proposition introuvable.");
        setReadyFor(id);
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  const loading = Boolean(id) && readyFor !== id;

  return (
    <main id="contenu-principal" className="min-h-screen bg-chalk px-4 py-8 text-ink">
      <div className="mx-auto max-w-2xl">
        <Link
          to="/mon-compte/propositions"
          className="text-sm font-medium text-ink hover:text-ballast"
        >
          ← Mes propositions
        </Link>
        {loading && <p className="mt-8 text-sm text-ballast">Chargement…</p>}
        {error && (
          <p role="alert" className="mt-8 text-sm text-brick">
            {error}
          </p>
        )}
        {proposal && !loading && <ProposalBody proposal={proposal} request={request} />}
      </div>
    </main>
  );
}

function ProposalBody({ proposal, request }: { proposal: Proposition; request: Demande | null }) {
  const searches = request?.recherches ?? [];
  const latest = searches.length > 0 ? searches[searches.length - 1] : null;
  const seats = new Map((latest?.resultats ?? []).map((r) => [r.id, r.places_restantes ?? null]));
  const changes = new Map((proposal.changements ?? []).map((c) => [c.id, c]));
  const advisor = advisorFirstName(proposal);
  const travelers = request?.demande.nombre_voyageurs;

  const known = new Set(SECTIONS.map((s) => s.type));
  const sections = [
    ...SECTIONS.map((s) => ({
      ...s,
      items: proposal.prestations.filter((p) => p.type === s.type),
    })),
    {
      type: "autre",
      title: "Et aussi",
      items: proposal.prestations.filter((p) => !known.has(p.type)),
    },
  ].filter((s) => s.items.length > 0);

  return (
    <article className="mt-6 space-y-8">
      <header>
        <p className="text-sm text-ballast">
          Votre proposition{request ? `, ${request.demande.destination}` : ""}
        </p>
        <h1 className="mt-1 font-display text-3xl font-extrabold tracking-tight sm:text-4xl">
          {proposal.titre}
        </h1>
        {request && <p className="mt-2 text-ballast">{tripSummary(request)}</p>}
      </header>

      {proposal.description && (
        <section aria-label="Message de votre conseiller" className="rounded-2xl bg-card p-5">
          <p className="whitespace-pre-line text-ink">{proposal.description}</p>
          <p className="mt-4 font-display font-extrabold">{advisor ?? "L'équipe DÉTOUR"}</p>
        </section>
      )}

      {sections.map((section) => (
        <section key={section.type} aria-labelledby={`section-${section.type}`}>
          <h2 id={`section-${section.type}`} className="mb-3 text-lg font-semibold">
            {section.title}
          </h2>
          <ul className="space-y-3">
            {section.items.map((item: Prestation) => (
              <ProposalService
                key={item.id}
                service={item}
                seats={seats.get(item.id) ?? null}
                change={changes.get(item.id)}
              />
            ))}
          </ul>
        </section>
      ))}

      <section aria-label="Total" className="rounded-2xl border border-ink p-5">
        <ProposalTotal proposition={proposal} travelers={travelers} large />
        <p className="mt-3 text-sm text-ink">
          {STATUS_SENTENCE[proposal.statut] ?? "Rien n'est réservé pour l'instant."}
        </p>
      </section>

      {!proposal.description && (
        <p className="font-display font-extrabold">{advisor ?? "L'équipe DÉTOUR"}</p>
      )}
    </article>
  );
}
