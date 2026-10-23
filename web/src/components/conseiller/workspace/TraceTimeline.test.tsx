import { describe, expect, it } from "vitest";
import { render, screen, within } from "@testing-library/react";
import { TraceTimeline } from "./TraceTimeline";
import type { Demande, Proposition } from "../../../types";

/*
 * #128: the agent trace shows every step with the right badge — the traveler
 * message, agent searches (suggestions), missing fields and agent drafts (à
 * relire), advisor corrections (relu) and advisor decisions (relu, or
 * confirmé when the request is qualified for proposal). The agent never
 * appears as the confirmer: a draft always stays "à relire".
 */

function makeDemande(overrides: Partial<Demande> = {}): Demande {
  return {
    id: "dem_1",
    statut: "nouveau",
    cree_le: "2026-10-20T10:00:00+00:00",
    demande: {
      type_voyage: "aventure",
      destination: "Nantes",
      date_depart: "2026-11-10",
      date_retour: "2026-11-14",
      nombre_voyageurs: 2,
      has_enfants: false,
      nombre_enfants: 0,
      budget_max_par_personne: 300,
      niveau_aventure: "moderate",
      besoin_guide: false,
      activites: [],
      contraintes: "",
      conseiller: "",
      souhaits: "",
      user_id: "usr_1",
    },
    ...overrides,
  };
}

function makeDraft(overrides: Partial<Proposition> = {}): Proposition {
  return {
    id: "prop_1",
    demande_id: "dem_1",
    statut: "brouillon",
    cree_le: "2026-10-21T09:00:00+00:00",
    modifiee_le: "2026-10-21T09:00:00+00:00",
    conseiller: "",
    titre: "Week-end à Nantes",
    description: "",
    prestations: [],
    prix_total_eur: 600,
    ...overrides,
  };
}

function section(label: string) {
  const heading = screen.getByText(label);
  return within(heading.parentElement as HTMLElement);
}

/** The trace entry (li) that owns the badge and the body text. */
function entryOf(container: ReturnType<typeof within>, text: RegExp) {
  return within(container.getByText(text).closest("li") as HTMLElement);
}

describe("TraceTimeline — empty and conversation", () => {
  it("renders nothing when there is no trace data", () => {
    const { container } = render(<TraceTimeline request={makeDemande()} propositions={[]} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("labels traveler and agent messages with VOYAGEUR and AGENT", () => {
    render(
      <TraceTimeline
        request={makeDemande({
          messages: [
            { role: "user", content: "Je veux partir à Nantes." },
            { role: "assistant", content: "Quel est votre budget ?" },
          ],
        })}
        propositions={[]}
      />,
    );
    const conv = section("Demande du voyageur");
    expect(entryOf(conv, /Je veux partir/).getByText("VOYAGEUR")).toBeInTheDocument();
    expect(entryOf(conv, /Quel est votre budget/).getByText("AGENT")).toBeInTheDocument();
  });
});

describe("TraceTimeline — agent suggestions", () => {
  it("shows SUGGESTION AGENT on verified searches with source and check date", () => {
    render(
      <TraceTimeline
        request={makeDemande({
          recherches: [
            {
              id: "rec_1",
              source_label: "Serveur fournisseur",
              source_url: "http://127.0.0.1:8765",
              consulte_le: "2026-10-22T09:40:00+00:00",
              criteres: {},
              resultats: [
                {
                  id: "train-nantes-01",
                  nom: "Train vers Nantes",
                  type: "transport",
                  destination: "Nantes",
                  prix_unitaire_eur: 96,
                  prix_total_eur: 288,
                  disponible: true,
                  dans_budget: true,
                },
              ],
            },
          ],
        })}
        propositions={[]}
      />,
    );
    const searches = section("Recherches de l’agent");
    const entry = entryOf(searches, /Recherche vérifiée/);
    expect(entry.getByText("SUGGESTION AGENT")).toBeInTheDocument();
    expect(entry.getByText(/Train vers Nantes \(train-nantes-01\)/)).toBeInTheDocument();
    expect(entry.getByText(/Vérifié le/)).toBeInTheDocument();
  });

  it("shows À RELIRE for missing required fields", () => {
    render(
      <TraceTimeline
        request={makeDemande({ champs_manquants: ["date_depart", "budget_max_par_personne"] })}
        propositions={[]}
      />,
    );
    const missing = section("Informations manquantes ou obsolètes");
    expect(missing.getByText("À RELIRE")).toBeInTheDocument();
    expect(missing.getByText(/date_depart, budget_max_par_personne/)).toBeInTheDocument();
  });

  it("marks agent drafts with À RELIRE and a Brouillon tag, never CONFIRMÉ", () => {
    render(<TraceTimeline request={makeDemande()} propositions={[makeDraft()]} />);
    const drafts = section("Brouillons de l’agent");
    const entry = entryOf(drafts, /Week-end à Nantes \(prop_1\)/);
    expect(entry.getByText("À RELIRE")).toBeInTheDocument();
    expect(entry.getByText("Brouillon")).toBeInTheDocument();
    expect(screen.queryByText("CONFIRMÉ")).not.toBeInTheDocument();
  });
});

describe("TraceTimeline — advisor corrections and decisions", () => {
  it("shows RELU CONSEILLER on field corrections with before → after", () => {
    render(
      <TraceTimeline
        request={makeDemande({
          modifications: [
            {
              champ: "date_depart",
              avant: "2026-11-10",
              apres: "2026-11-12",
              par: "conseiller_1",
              le: "2026-10-22T10:00:00+00:00",
            },
          ],
        })}
        propositions={[]}
      />,
    );
    const corrections = section("Corrections du conseiller");
    const entry = entryOf(corrections, /Correction : date_depart/);
    expect(entry.getByText("RELU CONSEILLER")).toBeInTheDocument();
    expect(entry.getByText(/2026-11-10 → 2026-11-12/)).toBeInTheDocument();
    expect(entry.getByText(/conseiller_1 ·/)).toBeInTheDocument();
  });

  it("shows CONFIRMÉ when the advisor qualifies the request for proposal", () => {
    render(
      <TraceTimeline
        request={makeDemande({
          decisions: [
            {
              action: "qualification",
              avant: "a_qualifier",
              apres: "pret_proposition",
              motif: "Demande complète",
              par: "conseiller_1",
              le: "2026-10-22T11:00:00+00:00",
            },
          ],
        })}
        propositions={[]}
      />,
    );
    const decisions = section("Décisions du conseiller");
    const entry = entryOf(decisions, /qualification → pret_proposition/);
    expect(entry.getByText("CONFIRMÉ")).toBeInTheDocument();
    expect(entry.getByText(/motif : Demande complète/)).toBeInTheDocument();
  });

  it("shows RELU CONSEILLER — not CONFIRMÉ — for a non-confirming decision", () => {
    render(
      <TraceTimeline
        request={makeDemande({
          decisions: [
            {
              action: "statut",
              avant: "nouveau",
              apres: "a_qualifier",
              motif: "Revue du dossier",
              par: "conseiller_1",
              le: "2026-10-22T11:30:00+00:00",
            },
          ],
        })}
        propositions={[]}
      />,
    );
    const decisions = section("Décisions du conseiller");
    expect(
      entryOf(decisions, /statut → a_qualifier/).getByText("RELU CONSEILLER"),
    ).toBeInTheDocument();
    expect(screen.queryByText("CONFIRMÉ")).not.toBeInTheDocument();
  });
});
