"use strict";

/* Scripts communs des pages : déconnexion, connexion, inscription, tableau de bord. */

const $ = (sel) => document.querySelector(sel);

async function apiJSON(path, options = {}) {
  const res = await fetch(path, { cache: "no-store", ...options });
  const data = await res.json();
  if (!res.ok) throw new Error(data.erreur?.message || "Erreur serveur.");
  return data;
}

function setError(id, message) {
  const node = document.getElementById(id);
  if (node) node.textContent = message || "";
}

async function postJSON(path, payload) {
  return apiJSON(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

/* ---------- Déconnexion (toutes les pages connectées) ---------- */

const logoutButton = document.getElementById("logout-button");
if (logoutButton) {
  logoutButton.hidden = false;
  logoutButton.addEventListener("click", async () => {
    try {
      await fetch("/api/logout", { method: "POST" });
    } catch (err) {
      /* la session expire côté serveur dans tous les cas */
    }
    window.location.href = "/login";
  });
}

/* ---------- Page de connexion ---------- */

const clientLoginForm = document.getElementById("client-login-form");
if (clientLoginForm) {
  clientLoginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    setError("login-error", "");
    try {
      await postJSON("/api/login", {
        email: $("#login-email").value,
        mot_de_passe: $("#login-mot-de-passe").value,
      });
      window.location.href = "/chat";
    } catch (err) {
      setError("login-error", err.message);
    }
  });
}

const toggleRegister = document.getElementById("toggle-register");
if (toggleRegister) {
  toggleRegister.addEventListener("click", () => {
    const registerForm = document.getElementById("register-form");
    const loginForm = document.getElementById("client-login-form");
    const backToLogin = document.createElement("button");
    registerForm.hidden = false;
    loginForm.hidden = true;
    toggleRegister.hidden = true;
    backToLogin.type = "button";
    backToLogin.className = "secondary-button";
    backToLogin.textContent = "← J'ai déjà un compte";
    backToLogin.addEventListener("click", () => {
      registerForm.hidden = true;
      loginForm.hidden = false;
      toggleRegister.hidden = false;
      backToLogin.remove();
    });
    registerForm.prepend(backToLogin);
  });
}

const registerForm = document.getElementById("register-form");
if (registerForm) {
  registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    setError("register-error", "");
    try {
      await postJSON("/api/register", {
        email: $("#register-email").value,
        nom: $("#register-nom").value,
        mot_de_passe: $("#register-mot-de-passe").value,
      });
      window.location.href = "/chat";
    } catch (err) {
      setError("register-error", err.message);
    }
  });
}

const conseillerLoginForm = document.getElementById("conseiller-login-form");
if (conseillerLoginForm) {
  conseillerLoginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    setError("conseiller-error", "");
    try {
      await postJSON("/api/login-conseiller", { cle: $("#conseiller-cle").value });
      window.location.href = "/conseiller";
    } catch (err) {
      setError("conseiller-error", err.message);
    }
  });
}

/* ---------- Tableau de bord conseiller ---------- */

const STATUT_LABELS = {
  nouvelle: "Nouvelle",
  a_analyser: "À analyser",
  a_revoir: "À revoir",
  propose: "Proposée",
  valide: "Validée",
  refuse: "Refusée",
};

const QUALIFICATION_LABELS = {
  incomplet: "Incomplète",
  en_cours: "En cours",
  pret_relecture: "Prête pour relecture",
  pret_proposition: "Prête pour proposition",
};

const TYPE_LABELS = {
  "trek-randonnee": "Trek / Randonnée",
  "lune-de-miel": "Lune de miel",
  "voyage-familial": "Voyage familial",
  autres: "Autres",
};

const NIVEAU_LABELS = { calme: "Calme", modere: "Modéré", intense: "Intense" };

function formatDateTime(iso) {
  const date = new Date(iso);
  return Number.isNaN(date.getTime())
    ? iso
    : date.toLocaleString("fr-FR", { dateStyle: "short", timeStyle: "short" });
}

function dashRow(demande) {
  const d = demande.demande;
  const client = demande.client;
  const tr = document.createElement("tr");
  tr.dataset.id = demande.id;

  const tdId = document.createElement("td");
  tdId.className = "dash-id";
  tdId.textContent = demande.id;

  const tdClient = document.createElement("td");
  tdClient.textContent = client ? `${client.nom} (${client.email})` : "—";

  const tdVoyage = document.createElement("td");
  tdVoyage.textContent = `${d.destination} · ${TYPE_LABELS[d.type_voyage] || d.type_voyage} · ${d.nombre_voyageurs} voyageur(s)`;

  const tdDates = document.createElement("td");
  tdDates.textContent = `${d.date_depart} → ${d.date_retour}`;

  const tdBudget = document.createElement("td");
  tdBudget.textContent = `${d.budget_max_par_personne} €/pers.`;

  const tdCree = document.createElement("td");
  tdCree.textContent = formatDateTime(demande.cree_le);

  const tdQualification = document.createElement("td");
  tdQualification.append(blocQualification(demande));

  const tdStatut = document.createElement("td");
  const select = document.createElement("select");
  select.className = "statut-select";
  select.setAttribute("aria-label", "Statut de la demande");
  for (const [valeur, label] of Object.entries(STATUT_LABELS)) {
    const option = document.createElement("option");
    option.value = valeur;
    option.textContent = label;
    option.selected = valeur === demande.statut;
    select.append(option);
  }
  select.addEventListener("change", async () => {
    tdStatut.classList.remove("statut-erreur");
    try {
      await apiJSON(`/api/demandes/${encodeURIComponent(demande.id)}/statut`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ statut: select.value }),
      });
    } catch (err) {
      select.value = demande.statut;
      tdStatut.classList.add("statut-erreur");
      tdStatut.title = err.message;
    }
  });
  tdStatut.append(select);

  const tdAction = document.createElement("td");
  const detailButton = document.createElement("button");
  detailButton.type = "button";
  detailButton.className = "secondary-button";
  detailButton.textContent = "Détail";
  detailButton.addEventListener("click", () => afficherDetail(demande.id));
  tdAction.append(detailButton);

  tr.append(tdId, tdClient, tdVoyage, tdDates, tdBudget, tdCree, tdQualification, tdStatut, tdAction);
  return tr;
}

function blocQualification(demande) {
  const bloc = document.createElement("div");
  bloc.className = "qualif-bloc";
  const label = document.createElement("div");
  label.className = "qualif-label";
  label.textContent = QUALIFICATION_LABELS[demande.qualification] || demande.qualification || "—";
  bloc.append(label);

  const actions = document.createElement("div");
  actions.className = "qualif-actions";
  actions.append(
    boutonQualification(demande, "incomplet", "Renvoyer en incomplet"),
    boutonQualification(demande, "pret_proposition", "Valider pour proposition"),
  );
  bloc.append(actions);
  return bloc;
}

function boutonQualification(demande, qualification, texte) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "secondary-button qualif-button";
  button.textContent = texte;
  button.disabled = demande.qualification === qualification;
  if (qualification === "pret_proposition" && (demande.champs_manquants || []).length) {
    button.title = "Informations obligatoires manquantes : " + demande.champs_manquants.join(", ");
  }
  button.addEventListener("click", () => changerQualification(demande, qualification, button));
  return button;
}

async function changerQualification(demande, qualification, button) {
  button.disabled = true;
  try {
    await apiJSON(`/api/demandes/${encodeURIComponent(demande.id)}/qualification`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ qualification }),
    });
    await chargerDemandes();
    const detail = document.getElementById("detail-section");
    if (detail && !detail.hidden) afficherDetail(demande.id);
  } catch (err) {
    button.disabled = false;
    setError("demandes-error", err.message);
  }
}

function detailChamp(label, valeur) {
  const div = document.createElement("div");
  div.className = "recap-item";
  const lbl = document.createElement("div");
  lbl.className = "recap-item-label";
  lbl.textContent = label;
  const val = document.createElement("div");
  val.className = "recap-item-value";
  val.textContent = valeur || "—";
  div.append(lbl, val);
  return div;
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
      content.append(bloc);
    }
  } catch (err) {
    const erreur = document.createElement("p");
    erreur.className = "form-error";
    erreur.textContent = err.message;
    content.append(erreur);
  }
}

async function afficherDetail(demId) {
  const content = document.getElementById("detail-content");
  const section = document.getElementById("detail-section");
  content.replaceChildren();
  section.hidden = false;
  try {
    const data = await apiJSON(`/api/demandes/${encodeURIComponent(demId)}`);
    const record = data.demande;
    const d = record.demande;

    const info = document.createElement("div");
    info.className = "source-box";
    info.append(Object.assign(document.createElement("div"), {
      textContent: `Demande ${record.id} — qualification : ${QUALIFICATION_LABELS[record.qualification] || record.qualification || "—"} — statut : ${STATUT_LABELS[record.statut] || record.statut}`,
    }));
    const client = record.client;
    info.append(Object.assign(document.createElement("div"), {
      textContent: client ? `Voyageur : ${client.nom} (${client.email})` : "Voyageur : —",
    }));
    const manquants = record.champs_manquants || [];
    if (manquants.length) {
      info.append(Object.assign(document.createElement("div"), {
        textContent: "Informations obligatoires manquantes : " + manquants.join(", "),
      }));
    }
    if (record.messages) {
      info.append(Object.assign(document.createElement("div"), {
        textContent: `${record.messages.length} message(s) dans la conversation.`,
      }));
    }
    content.append(info);

    const grid = document.createElement("div");
    grid.className = "recap-grid";
    grid.append(
      detailChamp("Type de voyage", TYPE_LABELS[d.type_voyage] || d.type_voyage),
      detailChamp("Destination", d.destination),
      detailChamp("Dates", `${d.date_depart} → ${d.date_retour}`),
      detailChamp("Voyageurs", String(d.nombre_voyageurs)),
      detailChamp("Enfants", d.has_enfants ? `${d.nombre_enfants} enfant(s)` : "Non"),
      detailChamp("Budget max / personne", `${d.budget_max_par_personne} €`),
      detailChamp("Niveau d'aventure", NIVEAU_LABELS[d.niveau_aventure] || d.niveau_aventure),
      detailChamp("Guide requis", d.besoin_guide ? "Oui" : "Non"),
      detailChamp("Activités", d.activites.length ? d.activites.join(", ") : ""),
      detailChamp("Allergies / contraintes", d.contraintes),
    );
    const souhaits = detailChamp("Souhaits / ambiance", d.souhaits);
    souhaits.classList.add("recap-full");
    grid.append(souhaits);
    content.append(grid);

    const recherches = record.recherches || [];
    if (recherches.length) {
      const derniere = recherches[recherches.length - 1];
      const titre = document.createElement("h3");
      titre.className = "detail-subtitle";
      titre.textContent = "Dernières prestations vérifiées";
      const source = document.createElement("div");
      source.className = "source-box";
      source.append(Object.assign(document.createElement("div"), {
        textContent: `Source : ${derniere.source_label} — vérifié le ${formatDateTime(derniere.consulte_le)}`,
      }));
      const liste = document.createElement("ul");
      liste.className = "detail-liste";
      for (const item of derniere.resultats) {
        const li = document.createElement("li");
        li.textContent = `${item.nom} (${item.id}) — ${item.prix_unitaire_eur} €/pers · ${item.prix_total_eur} € pour le groupe · ${item.disponible ? "disponible" : "indisponible"}`;
        liste.append(li);
      }
      content.append(titre, source, liste);
    } else {
      const aucune = document.createElement("p");
      aucune.className = "demande-empty";
      aucune.textContent = "Aucune recherche vérifiée pour cette demande.";
      content.append(aucune);
    }

    // Proposals for this request: each line keeps its own source and read time.
    await afficherPropositionsDemande(content, demId);
  } catch (err) {
    const erreur = document.createElement("p");
    erreur.className = "form-error";
    erreur.textContent = err.message;
    content.append(erreur);
  }
  section.scrollIntoView({ behavior: "smooth", block: "start" });
}

const demandesBody = document.getElementById("demandes-body");
if (demandesBody) {
  document.getElementById("detail-close").addEventListener("click", () => {
    document.getElementById("detail-section").hidden = true;
  });
  document.getElementById("refresh-demandes").addEventListener("click", chargerDemandes);
  chargerDemandes();
}

async function chargerDemandes() {
  const body = document.getElementById("demandes-body");
  const vide = document.getElementById("demandes-empty");
  setError("demandes-error", "");
  body.replaceChildren();
  try {
    const data = await apiJSON("/api/demandes");
    const demandes = data.demandes || [];
    vide.hidden = demandes.length > 0;
    for (const demande of demandes) body.append(dashRow(demande));
  } catch (err) {
    setError("demandes-error", err.message);
  }
}