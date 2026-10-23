import { formatDateTime } from "../../../lib/format";
import type { Demande, Proposition } from "../../../types";

/*
 * #128: agent trace timeline. The advisor follows what the traveler asked,
 * what the agent searched and suggested, and what the advisor corrected and
 * decided. Agent suggestions are drafts; only advisor decisions can be
 * confirmed — the agent never appears as the confirmer of anything.
 */

const ROLE_BADGES: Record<string, BadgeKey> = {
  user: "voyageur",
  assistant: "agent",
};

type BadgeKey = "voyageur" | "agent" | "suggestion" | "a_relever" | "revu" | "confirme";

const BADGE_STYLES: Record<BadgeKey, string> = {
  voyageur: "text-ink border-sky bg-sky",
  agent: "text-ballast border-line bg-card",
  suggestion: "text-ink border-yellow bg-yellow/15",
  a_relever: "text-ballast border-dashed border-ballast bg-chalk",
  revu: "text-ink border-sky bg-sky",
  confirme: "text-chalk border-ink bg-ink",
};

const BADGE_LABELS: Record<BadgeKey, string> = {
  voyageur: "VOYAGEUR",
  agent: "AGENT",
  suggestion: "SUGGESTION AGENT",
  a_relever: "À RELIRE",
  revu: "RELU CONSEILLER",
  confirme: "CONFIRMÉ",
};

interface TraceTimelineProps {
  request: Demande;
  propositions: Proposition[];
}

interface TraceItem {
  badge: BadgeKey;
  body: string;
  meta?: string;
  draft?: boolean;
}

interface TraceSection {
  label: string;
  items: TraceItem[];
}

/** #128: ordered trace of the conversation, agent searches, drafts, corrections and advisor decisions. */
export function TraceTimeline({ request, propositions }: TraceTimelineProps) {
  const messages = request.messages ?? [];
  const searches = request.recherches ?? [];
  const missing = request.champs_manquants ?? [];
  const decisions = request.decisions ?? [];
  const modifications = request.modifications ?? [];
  const drafts = propositions.filter((p) => p.statut === "brouillon");

  if (
    messages.length === 0 &&
    searches.length === 0 &&
    missing.length === 0 &&
    decisions.length === 0 &&
    modifications.length === 0 &&
    propositions.length === 0
  ) {
    return null;
  }

  const sections: TraceSection[] = [];

  if (messages.length > 0) {
    sections.push({
      label: "Demande du voyageur",
      items: messages.map((m) => ({
        badge: ROLE_BADGES[m.role] ?? "agent",
        body: m.content || "—",
      })),
    });
  }

  if (searches.length > 0) {
    sections.push({
      label: "Recherches de l’agent",
      items: searches.map((r) => {
        const lines = (r.resultats ?? []).map(
          (p) =>
            `${p.nom} (${p.id}) — ${p.prix_unitaire_eur} €/pers · ${
              p.prix_total_eur != null ? `${p.prix_total_eur} €` : "—"
            } · ${p.disponible ? "disponible" : "indisponible"}`,
        );
        return {
          badge: "suggestion" as BadgeKey,
          body: `Recherche vérifiée — Source : ${r.source_label || "—"}\n${lines.join("\n")}`,
          meta: `Vérifié le ${formatDateTime(r.consulte_le)}`,
        };
      }),
    });
  }

  if (missing.length > 0) {
    sections.push({
      label: "Informations manquantes ou obsolètes",
      items: [
        {
          badge: "a_relever" as BadgeKey,
          body: `Champs obligatoires manquants : ${missing.join(", ")}`,
        },
      ],
    });
  }

  if (drafts.length > 0) {
    sections.push({
      label: "Brouillons de l’agent",
      items: drafts.map((p) => ({
        badge: "a_relever" as BadgeKey,
        body: `${p.titre || "Proposition"} (${p.id}) — total ${
          p.prix_total_eur != null ? `${p.prix_total_eur} €` : "—"
        }`,
        draft: true,
      })),
    });
  }

  if (modifications.length > 0) {
    sections.push({
      label: "Corrections du conseiller",
      items: modifications.map((m) => ({
        badge: "revu" as BadgeKey,
        body: `Correction : ${m.champ || "champ"} ${
          m.avant != null ? String(m.avant) : "—"
        } → ${m.apres != null ? String(m.apres) : "—"}`,
        meta: `${m.par || "—"} · ${formatDateTime(m.le)}`,
      })),
    });
  }

  if (decisions.length > 0) {
    sections.push({
      label: "Décisions du conseiller",
      items: decisions.map((d) => {
        const isConfirmation =
          (d.action === "qualification" && d.apres === "pret_proposition") ||
          (d.action === "statut" && d.apres === "valide");
        return {
          badge: (isConfirmation ? "confirme" : "revu") as BadgeKey,
          body: `${d.action}${d.apres ? ` → ${d.apres}` : ""} — motif : ${d.motif || "—"}`,
          meta: `${d.par || "—"} · ${formatDateTime(d.le)}`,
        };
      }),
    });
  }

  return (
    <section aria-labelledby="trace-timeline-title" className="space-y-3">
      <h3 id="trace-timeline-title" className="text-sm font-semibold text-ink">
        Trace de la conversation
      </h3>
      <ol className="space-y-2">
        {sections.map((section) => (
          <li key={section.label} className="space-y-2">
            <p className="font-mono text-[11px] font-semibold tracking-widest text-ballast uppercase">
              {section.label}
            </p>
            <ul className="space-y-2">
              {section.items.map((item, i) => (
                <li
                  key={`${section.label}-${i}`}
                  className="flex items-start gap-3 rounded-xl border border-line bg-card px-4 py-3 text-sm leading-relaxed text-ink"
                >
                  <span
                    className={`mt-0.5 shrink-0 rounded-full border px-2.5 py-0.5 font-mono text-[10px] font-semibold tracking-widest whitespace-nowrap uppercase ${BADGE_STYLES[item.badge]}`}
                  >
                    {BADGE_LABELS[item.badge]}
                  </span>
                  <span className="min-w-0">
                    {item.draft && (
                      <span className="mb-1.5 inline-block rounded-full border border-brick px-2 py-0.5 font-mono text-[10px] font-semibold tracking-widest text-brick uppercase">
                        Brouillon
                      </span>
                    )}
                    <span className={`whitespace-pre-wrap ${item.draft ? "block" : ""}`}>
                      {item.body}
                    </span>
                    {item.meta && (
                      <span className="mt-1 block font-mono text-[11px] text-ballast">
                        {item.meta}
                      </span>
                    )}
                  </span>
                </li>
              ))}
            </ul>
          </li>
        ))}
      </ol>
    </section>
  );
}
