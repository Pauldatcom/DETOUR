"use strict";

/**
 * Proposal detail UI for the advisor dashboard: provenance, reading deltas,
 * and keep/replace/drop decisions. Relies on helpers from pages.js (apiJSON,
 * formatDateTime, afficherDetail).
 */

const DECISION_LABELS = {
  keep: "Garder",
  replace: "Remplacer",
  drop: "Retirer",
};

/** Statuts d'une proposition (miroir de utils.py). */
const PROP_STATUT_LABELS = {
  brouillon: "Brouillon",
  envoyee: "Envoyée",
  validee: "Validée",
  refusee: "Refusée",
  correction_requested: "Correction demandée",
};

/** Décisions du conseiller sur une proposition (#28, #32, #36). */
const DECISION_PROPOSITION = [
  { action: "accepter", route: "accepter", label: "Accepter", motif: false },
  {
    action: "demander_correction",
    route: "correction",
    label: "Demander une correction",
    motif: true,
  },
  { action: "refuser", route: "refuser", label: "Refuser", motif: true },
];

/**
 * #128 : badge de décision distinguant la provenance et l'étape de validation.
 * L'agent propose ("Suggestion de l'agent"), le conseiller relit et confirme.
 * L'agent ne apparaît jamais comme l'auteur de la confirmation.
 */
const DECISION_BADGE = {
  brouillon: { label: "Suggestion de l'agent · à relire", kind: "agent" },
  envoyee: { label: "Relu par le conseiller", kind: "relu" },
  correction_requested: { label: "Relu par le conseiller", kind: "relu" },
  validee: { label: "Confirmé par le conseiller", kind: "confirme" },
  refusee: { label: "Refusé par le conseiller", kind: "ko" },
};

/** Crée un badge de décision avec la classe appropriée. */
function badgeDecision(statut) {
  const def = DECISION_BADGE[statut] || { label: statut, kind: "info" };
  const span = document.createElement("span");
  span.className = `badge badge-${def.kind}`;
  span.textContent = def.label;
  return span;
}

/**
 * Bloc de décision du conseiller sur une proposition.
 *
 * Affiche le statut, propose Accepter / Demander une correction / Refuser,
 * demande le motif quand l'action l'exige, puis confirme l'action et le
 * nouveau statut. La décision reste écrite côté serveur.
 */
function blocDecisionProposition(prop, demId) {
  const wrap = document.createElement("div");
  wrap.className = "prop-decision";

  const statut = document.createElement("div");
  statut.className = "prop-statut";
  statut.textContent = `Statut : ${PROP_STATUT_LABELS[prop.statut] || prop.statut}`;

  // #128 : badge de décision distinguant l'origine de la proposition.
  // L'agent suggère, le conseiller relit et confirme — jamais l'inverse.
  const badge = badgeDecision(prop.statut);

  const champs = document.createElement("div");
  champs.className = "prop-motif";
  champs.hidden = true;

  const motif = document.createElement("textarea");
  motif.className = "prop-motif-input";
  motif.rows = 2;
  motif.placeholder = "Motif (obligatoire)";
  motif.setAttribute("aria-label", "Motif de la décision");

  const instructions = document.createElement("textarea");
  instructions.className = "prop-motif-input";
  instructions.rows = 2;
  instructions.placeholder = "Instructions de correction (obligatoire)";
  instructions.setAttribute("aria-label", "Instructions de correction");
  instructions.hidden = true;

  champs.append(motif, instructions);

  const actions = document.createElement("div");
  actions.className = "prop-actions";
  const erreur = document.createElement("div");
  erreur.className = "form-error";
  const confirmation = document.createElement("div");
  confirmation.className = "prop-confirmation";

  async function envoyer(decision, bouton) {
    erreur.textContent = "";
    const corps = { motif: motif.value.trim() };
    if (decision.action === "demander_correction") {
      corps.instructions = instructions.value.trim();
    }
    for (const autre of actions.querySelectorAll("button")) {
      autre.disabled = true;
    }
    try {
      const data = await apiJSON(
        `/api/propositions/${encodeURIComponent(prop.id)}/${decision.route}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(corps),
        },
      );
      const apres = (data.proposition || {}).statut;
      const libelle = PROP_STATUT_LABELS[apres] || apres;
      statut.textContent = `Statut : ${libelle}`;
      // #128 : met à jour le badge de décision après l'action du conseiller.
      badge.replaceWith(badgeDecision(apres));
      confirmation.textContent = `${decision.label} — nouveau statut : ${libelle}.`;
      champs.hidden = true;
    } catch (err) {
      erreur.textContent = err.message;
      for (const autre of actions.querySelectorAll("button")) {
        autre.disabled = false;
      }
    }
  }

  for (const decision of DECISION_PROPOSITION) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "secondary-button";
    btn.textContent = decision.label;
    btn.addEventListener("click", () => {
      if (!decision.motif) {
        void envoyer(decision, btn);
        return;
      }
      // Le motif n'est demandé que pour les actions qui l'exigent.
      if (champs.hidden) {
        champs.hidden = false;
        instructions.hidden = decision.action !== "demander_correction";
        motif.focus();
        return;
      }
      void envoyer(decision, btn);
    });
    actions.append(btn);
  }

  wrap.append(statut, badge, actions, champs, confirmation, erreur);
  return wrap;
}

/** Form to keep / replace / drop a changed line (stores choice only — no send, no option). */
function formDecisionPrestation(propId, changement, demId) {
  const wrap = document.createElement("div");
  wrap.className = "decision-form";
  const motif = document.createElement("input");
  motif.type = "text";
  motif.placeholder = "Motif (obligatoire)";
  motif.setAttribute("aria-label", "Motif de la décision");
  const remp = document.createElement("input");
  remp.type = "text";
  remp.placeholder = "Id remplacement (si Remplacer)";
  remp.setAttribute("aria-label", "Identifiant de la prestation de remplacement");
  const erreur = document.createElement("div");
  erreur.className = "form-error";
  const actions = document.createElement("div");
  for (const [choix, label] of Object.entries(DECISION_LABELS)) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "secondary-button";
    btn.textContent = label;
    btn.addEventListener("click", async () => {
      erreur.textContent = "";
      btn.disabled = true;
      try {
        const body = {
          prestation_id: changement.id,
          choix,
          motif: motif.value,
        };
        if (choix === "replace") {
          body.remplacement_id = remp.value;
        }
        await apiJSON(`/api/propositions/${encodeURIComponent(propId)}/decisions`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
        await afficherDetail(demId);
      } catch (err) {
        erreur.textContent = err.message;
        btn.disabled = false;
      }
    });
    actions.append(btn);
  }
  wrap.append(motif, remp, actions, erreur);
  return wrap;
}

/** Human-readable delta between proposal v1 and a newer server reading. */
function texteChangementLecture(c) {
  if (c.inchange) {
    return `${c.nom} (${c.id}) — prix et disponibilité inchangés (${c.prix_apres} €/pers, ${c.disponible_apres ? "disponible" : "indisponible"})`;
  }
  const parts = [`${c.nom} (${c.id})`];
  if (c.prix_change) {
    parts.push(`prix ${c.prix_avant} € → ${c.prix_apres} €`);
  }
  if (c.disponibilite_change) {
    parts.push(c.disponible_apres ? "devenu disponible" : "indisponible");
  } else if (!c.disponible_apres) {
    parts.push("indisponible");
  }
  return parts.join(" — ");
}

/** Render stored proposals: verified lines show price, source and time; others stay missing. */
async function afficherPropositionsDemande(content, demId, propsData) {
  try {
    let props;
    if (propsData) {
      props = propsData;
    } else {
      const data = await apiJSON("/api/propositions");
      props = (data.propositions || []).filter((p) => p.demande_id === demId);
    }
    const titre = document.createElement("h3");
    titre.className = "detail-subtitle";
    titre.textContent = "Propositions";
    content.append(titre);
    if (!props.length) {
      const vide = document.createElement("p");
      vide.className = "demande-empty";
      vide.textContent = "Aucune proposition pour cette demande.";
      content.append(vide);
      return;
    }
    for (const prop of props) {
      const bloc = document.createElement("div");
      bloc.className = "source-box";
      const version = prop.version || 1;
      const lienParent = prop.parente_id ? ` · v${version} (depuis ${prop.parente_id})` : ` · v${version}`;
      bloc.append(Object.assign(document.createElement("div"), {
        textContent: `${prop.titre} (${prop.id})${lienParent} — total ${prop.prix_total_eur} €`,
      }));
      // Statut et décisions du conseiller sur la proposition (#36).
      bloc.append(blocDecisionProposition(prop, demId));
      const liste = document.createElement("ul");
      liste.className = "detail-liste";
      for (const item of prop.prestations || []) {
        // #127 : état de vérification explicite par ligne (vérifié / modifié / indisponible / manquant).
        liste.append(lignePrestationVerifiee(item, true));
      }
      bloc.append(liste);
      // #41: constraints the program checked against this proposal.
      const contraintes = prop.contraintes_verifiees || [];
      if (contraintes.length) {
        const titreC = document.createElement("div");
        titreC.textContent = "Contraintes prises en compte :";
        const listeC = document.createElement("ul");
        listeC.className = "detail-liste";
        for (const c of contraintes) {
          const li = document.createElement("li");
          const marque =
            c.statut === "ok" ? "✅" : c.statut === "non_respectee" ? "❌" : "⚠️";
          li.textContent = `${marque} ${c.detail}`;
          listeC.append(li);
        }
        bloc.append(titreC, listeC);
      }
      // Newer reading vs v1: previous/new price, unavailable, or unchanged.
      const changements = prop.changements || [];
      if (changements.length) {
        const sous = document.createElement("ul");
        sous.className = "detail-liste";
        for (const c of changements) {
          const li = document.createElement("li");
          li.textContent = texteChangementLecture(c);
          sous.append(li);
          if (!c.inchange) {
            li.append(formDecisionPrestation(prop.id, c, demId));
          }
        }
        bloc.append(Object.assign(document.createElement("div"), {
          textContent: "Nouvelle lecture :",
        }), sous);
      }
      const decisions = prop.decisions || [];
      if (decisions.length) {
        const titreDec = document.createElement("div");
        titreDec.textContent = "Décisions conseiller :";
        const listeDec = document.createElement("ul");
        listeDec.className = "detail-liste";
        for (const d of decisions) {
          const li = document.createElement("li");
          li.textContent =
            `${d.prestation_id} — ${DECISION_LABELS[d.choix] || d.choix}` +
            ` · ${d.par} · ${formatDateTime(d.le)} · ${d.motif}`;
          listeDec.append(li);
        }
        bloc.append(titreDec, listeDec);
      }
      // Historique des décisions sur la proposition elle-même.
      const decisionsStatut = prop.decisions_statut || [];
      if (decisionsStatut.length) {
        const titreStatut = document.createElement("div");
        titreStatut.textContent = "Décisions sur la proposition :";
        const listeStatut = document.createElement("ul");
        listeStatut.className = "detail-liste";
        for (const d of decisionsStatut) {
          const li = document.createElement("li");
          const action = DECISION_PROPOSITION.find(
            (x) => x.action === d.action,
          );
          const parties = [action ? action.label : d.action];
          if (d.motif) parties.push(d.motif);
          if (d.instructions) parties.push(d.instructions);
          li.textContent =
            `${parties.join(" — ")} · ${d.par} · ${formatDateTime(d.le)}` +
            (d.version ? ` · v${d.version}` : "");
          listeStatut.append(li);
        }
        bloc.append(titreStatut, listeStatut);
      }
      content.append(bloc);
    }
  } catch (err) {
    const erreur = document.createElement("p");
    erreur.className = "form-error";
    erreur.textContent = err.message;
    content.append(erreur);
  }
}
