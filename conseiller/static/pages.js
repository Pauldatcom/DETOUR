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

/**
 * #113 : joue le saut du O une seule fois (1,15 s, pas de boucle).
 * Lancé uniquement par la confirmation du conseiller (action « accepter »,
 * appelé depuis pages-propositions.js) — l'agent ne déclenche jamais
 * cette animation et le logo reste immobile au chargement de la page.
 * Respecte prefers-reduced-motion: reduce (état final sans mouvement).
 */
function jouerSautLogo() {
  var logo = document.querySelector(".brand .logo");
  if (!logo) return;
  if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  logo.classList.remove("play");
  void logo.getBoundingClientRect();
  logo.classList.add("play");
  setTimeout(function () { logo.classList.remove("play"); }, 1150);
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

  const tdEcheance = document.createElement("td");
  tdEcheance.className = "dash-echeance";
  // #51 : deadline status (target 24h open hours, max 48h) drives the badge.
  if (demande.echeance_statut === "depassee") {
    tdEcheance.classList.add("echeance-depassee");
  } else if (demande.echeance_statut === "approche") {
    tdEcheance.classList.add("echeance-approche");
  }
  tdEcheance.textContent =
    demande.echeance_cible ? formatDateTime(demande.echeance_cible) : "—";

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
    const motif = demanderMotif(
      `Passer la demande en « ${STATUT_LABELS[select.value]} »`,
    );
    if (motif === null) {
      select.value = demande.statut;
      return;
    }
    try {
      await apiJSON(`/api/demandes/${encodeURIComponent(demande.id)}/statut`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ statut: select.value, motif }),
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

  tr.append(tdId, tdClient, tdVoyage, tdDates, tdBudget, tdCree, tdEcheance, tdQualification, tdStatut, tdAction);
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
  const motif = demanderMotif(
    qualification === "pret_proposition"
      ? "Valider la demande pour proposition"
      : "Renvoyer la demande en incomplet",
  );
  if (motif === null) return;
  button.disabled = true;
  try {
    await apiJSON(`/api/demandes/${encodeURIComponent(demande.id)}/qualification`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ qualification, motif }),
    });
    await chargerDemandes();
    const detail = document.getElementById("detail-section");
    if (detail && !detail.hidden) afficherDetail(demande.id);
  } catch (err) {
    button.disabled = false;
    setError("demandes-error", err.message);
  }
}

/**
 * Demande le motif d'une décision. Toute décision doit être motivée :
 * l'auteur, la date et la raison sont conservés dans le journal.
 * Renvoie null si le conseiller annule.
 */
function demanderMotif(question) {
  const reponse = window.prompt(`${question}\nMotif (obligatoire) :`);
  if (reponse === null) return null;
  const motif = reponse.trim();
  if (!motif) {
    window.alert("Le motif de la décision est obligatoire.");
    return demanderMotif(question);
  }
  return motif;
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

const TRACE_BADGES = {
  user: { className: "trace-badge voyageur", label: "VOYAGEUR" },
  assistant: { className: "trace-badge agent", label: "AGENT" },
  suggestion: { className: "trace-badge agent-suggestion", label: "SUGGESTION AGENT" },
  a_relever: { className: "trace-badge a-relever", label: "\u00c0 RELIRE" },
  revu: { className: "trace-badge revu", label: "RELU CONSEILLER" },
  confirme: { className: "trace-badge confirme", label: "CONFIRM\u00c9" },
};

function traceEntry(badge, bodyText, opts) {
  opts = opts || {};
  const entry = document.createElement("li");
  entry.className = "trace-entry";
  const badgeNode = document.createElement("span");
  badgeNode.className = badge.className;
  badgeNode.textContent = badge.label;
  const corps = document.createElement("div");
  corps.className = "trace-entry-body";
  if (opts.draft) {
    const draft = document.createElement("span");
    draft.className = "trace-draft";
    draft.textContent = "Brouillon";
    corps.append(draft);
  }
  const text = document.createElement("div");
  text.textContent = bodyText;
  corps.append(text);
  if (opts.meta) {
    const meta = document.createElement("div");
    meta.className = "trace-meta";
    meta.textContent = opts.meta;
    corps.append(meta);
  }
  entry.append(badgeNode, corps);
  return entry;
}

function traceSectionLabel(text) {
  const li = document.createElement("li");
  li.className = "trace-section-label";
  li.textContent = text;
  return li;
}

/**
 * #128 : trace de l'agent — conversation, recherches vérifiées,
 * brouillons, modifications et décisions du conseiller, avec des badges
 * distinguant les suggestions de l'agent des décisions du conseiller.
 */
function afficherTrace(content, record, propositions) {
  const messages = record.messages || [];
  const recherches = record.recherches || [];
  const manquants = record.champs_manquants || [];
  const decisions = record.decisions || [];
  const modifications = record.modifications || [];
  const props = propositions || [];
  const brouillons = props.filter(function (p) { return p.statut === "brouillon"; });

  if (!messages.length && !recherches.length && !manquants.length
      && !decisions.length && !modifications.length && !props.length) return;

  const titre = document.createElement("h3");
  titre.className = "detail-subtitle";
  titre.textContent = "Trace de la conversation";
  const liste = document.createElement("ul");
  liste.className = "trace-list";

  // 1. Conversation
  if (messages.length) {
    liste.append(traceSectionLabel("Demande du voyageur"));
    for (const message of messages) {
      const badge = TRACE_BADGES[message.role] || TRACE_BADGES.assistant;
      liste.append(traceEntry(badge, message.content || "\u2014"));
    }
  }

  // 2. Recherches agent (suggestions)
  if (recherches.length) {
    liste.append(traceSectionLabel("Recherches de l\u2019agent"));
    for (const recherche of recherches) {
      const source = recherche.source_label || "\u2014";
      const dateStr = formatDateTime(recherche.consulte_le);
      const resultats = recherche.resultats || [];
      const lignes = resultats.map(function (r) {
        return r.nom + " (" + r.id + ") \u2014 " + r.prix_unitaire_eur
          + " \u20ac/pers \u00b7 " + (r.prix_total_eur != null ? r.prix_total_eur + " \u20ac" : "\u2014")
          + " \u00b7 " + (r.disponible ? "disponible" : "indisponible");
      });
      const body = "Recherche v\u00e9rifi\u00e9e \u2014 Source : " + source + "\n" + lignes.join("\n");
      liste.append(traceEntry(TRACE_BADGES.suggestion, body, { meta: "V\u00e9rifi\u00e9 le " + dateStr }));
    }
  }

  // 3. Informations manquantes
  if (manquants.length) {
    liste.append(traceSectionLabel("Informations manquantes ou obsol\u00e8tes"));
    liste.append(traceEntry(
      TRACE_BADGES.a_relever,
      "Champs obligatoires manquants : " + manquants.join(", "),
    ));
  }

  // 4. Brouillons (propositions agent)
  if (brouillons.length) {
    liste.append(traceSectionLabel("Brouillons de l\u2019agent"));
    for (const prop of brouillons) {
      liste.append(traceEntry(
        TRACE_BADGES.a_relever,
        (prop.titre || "Proposition") + " (" + prop.id + ") \u2014 total "
          + (prop.prix_total_eur != null ? prop.prix_total_eur + " \u20ac" : "\u2014"),
        { draft: true },
      ));
    }
  }

  // 5. Modifications conseiller (corrections de champs)
  if (modifications.length) {
    liste.append(traceSectionLabel("Corrections du conseiller"));
    for (const mod of modifications) {
      const champ = mod.champ || "champ";
      liste.append(traceEntry(
        TRACE_BADGES.revu,
        "Correction : " + champ + " "
          + (mod.avant != null ? mod.avant : "\u2014") + " \u2192 "
          + (mod.apres != null ? mod.apres : "\u2014"),
        { meta: (mod.par || "\u2014") + " \u00b7 " + formatDateTime(mod.le) },
      ));
    }
  }

  // 6. D\u00e9cisions conseiller (qualification, statut, confirmation)
  if (decisions.length) {
    liste.append(traceSectionLabel("D\u00e9cisions du conseiller"));
    for (const dec of decisions) {
      const isConfirmation = (dec.action === "qualification" && dec.apres === "pret_proposition")
        || (dec.action === "statut" && dec.apres === "valide");
      const badge = isConfirmation ? TRACE_BADGES.confirme : TRACE_BADGES.revu;
      liste.append(traceEntry(
        badge,
        dec.action + (dec.apres ? " \u2192 " + dec.apres : "") + " \u2014 motif : " + (dec.motif || "\u2014"),
        { meta: (dec.par || "\u2014") + " \u00b7 " + formatDateTime(dec.le) },
      ));
    }
  }

  content.append(titre, liste);
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

    // #128 : fetch propositions for the trace (brouillons + decisions).
    let propositions = [];
    try {
      const propData = await apiJSON("/api/propositions");
      propositions = (propData.propositions || []).filter(
        (p) => p.demande_id === demId,
      );
    } catch {
      // propositions section will show its own error
    }

    // #128 : trace agent (conversation + recherches + brouillons + decisions).
    afficherTrace(content, record, propositions);

    // Proposals for this request: each line keeps its own source and read time.
    await afficherPropositionsDemande(content, demId, propositions);
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
    // #51 : requests are displayed ordered by response deadline (most urgent first).
    const JAMMAIS = new Date(8640000000000000).getTime();
    const demandes = (data.demandes || []).sort(
      (a, b) => new Date(a.echeance_cible || JAMMAIS).getTime()
             - new Date(b.echeance_cible || JAMMAIS).getTime(),
    );
    vide.hidden = demandes.length > 0;
    for (const demande of demandes) body.append(dashRow(demande));
  } catch (err) {
    setError("demandes-error", err.message);
  }
}