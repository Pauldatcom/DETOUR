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

/** Form to keep / replace / drop a changed line (stores choice only — no send, no option). */
function formDecisionPrestation(propId, changement, demId) {
  const wrap = document.createElement("div");
  wrap.className = "decision-form";
  const motif = document.createElement("input");
  motif.type = "text";
  motif.placeholder = "Motif (obligatoire)";
  motif.setAttribute("aria-label", "Motif de la décision");
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
        await apiJSON(`/api/propositions/${encodeURIComponent(propId)}/decisions`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            prestation_id: changement.id,
            choix,
            motif: motif.value,
          }),
        });
        await afficherDetail(demId);
      } catch (err) {
        erreur.textContent = err.message;
        btn.disabled = false;
      }
    });
    actions.append(btn);
  }
  wrap.append(motif, actions, erreur);
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
async function afficherPropositionsDemande(content, demId) {
  try {
    const data = await apiJSON("/api/propositions");
    const props = (data.propositions || []).filter((p) => p.demande_id === demId);
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
      bloc.append(Object.assign(document.createElement("div"), {
        textContent: `${prop.titre} (${prop.id}) — total ${prop.prix_total_eur} €`,
      }));
      const liste = document.createElement("ul");
      liste.className = "detail-liste";
      for (const item of prop.prestations || []) {
        const li = document.createElement("li");
        if (item.verification === "verifie") {
          const dispo = item.disponible ? "disponible" : "indisponible";
          li.textContent =
            `${item.nom} (${item.id}) — ${item.prix_unitaire_eur} €/pers · ${dispo}` +
            ` · ${item.source} · ${formatDateTime(item.consulte_le)}`;
        } else {
          li.textContent = `${item.nom} (${item.id}) — manquant`;
        }
        liste.append(li);
      }
      bloc.append(liste);
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
      content.append(bloc);
    }
  } catch (err) {
    const erreur = document.createElement("p");
    erreur.className = "form-error";
    erreur.textContent = err.message;
    content.append(erreur);
  }
}
