"use strict";

const $ = (sel) => document.querySelector(sel);
const state = { messages: [], demandeId: null };

const TYPE_LABELS = {
  "trek-randonnee": "Trek / Randonnée",
  "lune-de-miel": "Lune de miel",
  "voyage-familial": "Voyage familial",
  "autres": "Autres",
};

const NIVEAU_LABELS = { calme: "Calme", modere: "Modéré", intense: "Intense" };

const TYPE_PRESTATION_LABELS = { transport: "Transport", hebergement: "Hébergement", activite: "Activité" };

const WELCOME = "Bonjour ! Je suis l'assistant voyage de DÉTOUR. Décrivez-moi le voyage que vous imaginez : destination, dates, nombre de voyageurs, budget… et je vérifie ce qui est disponible dans notre catalogue.";

async function api(path, options = {}) {
  const res = await fetch(path, { cache: "no-store", ...options });
  const data = await res.json();
  if (!res.ok) throw new Error(data.erreur?.message || "Erreur serveur.");
  return data;
}

function formatDate(iso) {
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? iso : date.toLocaleString("fr-FR", { dateStyle: "long", timeStyle: "short" });
}

function recapItem(label, value) {
  const div = document.createElement("div");
  div.className = "recap-item";
  const lbl = document.createElement("div");
  lbl.className = "recap-item-label";
  lbl.textContent = label;
  const val = document.createElement("div");
  val.className = "recap-item-value";
  val.textContent = value || "—";
  div.append(lbl, val);
  return div;
}

function renderRecap(demande) {
  const d = demande.demande;
  const content = $("#recap-content");
  content.replaceChildren();

  const wrap = document.createElement("div");
  wrap.className = "recap";

  const header = document.createElement("div");
  header.className = "recap-header";
  const h3 = document.createElement("h3");
  h3.textContent = "Demande " + demande.id;
  const statut = document.createElement("span");
  statut.className = "recap-statut";
  statut.textContent = "À analyser";
  header.append(h3, statut);
  wrap.append(header);

  const grid = document.createElement("div");
  grid.className = "recap-grid";
  grid.append(
    recapItem("Type de voyage", TYPE_LABELS[d.type_voyage] || d.type_voyage),
    recapItem("Destination", d.destination),
    recapItem("Date de départ", d.date_depart),
    recapItem("Date de retour", d.date_retour),
    recapItem("Nombre de voyageurs", String(d.nombre_voyageurs)),
    recapItem("Enfants", d.has_enfants ? `${d.nombre_enfants} enfant(s)` : "Non"),
    recapItem("Budget max / personne", `${d.budget_max_par_personne} €`),
    recapItem("Niveau d'aventure", NIVEAU_LABELS[d.niveau_aventure] || d.niveau_aventure),
    recapItem("Guide requis", d.besoin_guide ? "Oui" : "Non"),
    recapItem("Activités", d.activites.length ? d.activites.join(", ") : "—"),
  );

  if (d.contraintes) {
    const c = recapItem("Allergies / contraintes", d.contraintes);
    c.classList.add("recap-full");
    grid.append(c);
  }

  if (d.souhaits) {
    const s = recapItem("Souhaits / ambiance", d.souhaits);
    s.classList.add("recap-full");
    grid.append(s);
  }

  wrap.append(grid);
  content.append(wrap);

  state.demandeId = demande.id;
  $("#search-results").replaceChildren();
  $("#search-error").textContent = "";
  $("#search-section").hidden = false;
  $("#recap-section").hidden = false;
  $("#recap-section").scrollIntoView({ behavior: "smooth", block: "start" });
}

function badge(text, kind) {
  const span = document.createElement("span");
  span.className = `badge badge-${kind}`;
  span.textContent = text;
  return span;
}

function renderPrestation(item) {
  const card = document.createElement("article");
  card.className = "offer-card" + (item.disponible ? "" : " offer-unavailable");

  const top = document.createElement("div");
  top.className = "offer-card-top";
  const type = document.createElement("span");
  type.className = "offer-type";
  type.textContent = TYPE_PRESTATION_LABELS[item.type] || item.type;
  const id = document.createElement("span");
  id.className = "offer-id";
  id.textContent = item.id;
  top.append(type, id);

  const title = document.createElement("h3");
  title.textContent = item.nom;
  const dest = document.createElement("div");
  dest.className = "offer-destination";
  dest.textContent = item.destination;
  const desc = document.createElement("p");
  desc.textContent = item.description;

  const badges = document.createElement("div");
  badges.className = "badges";
  badges.append(item.disponible
    ? badge(`Disponible · ${item.places_restantes} place(s)`, "ok")
    : badge(`Indisponible · ${item.places_restantes} place(s)`, "ko"));
  if (item.dans_budget === true) badges.append(badge("Dans le budget", "ok"));
  if (item.dans_budget === false) badges.append(badge("Hors budget", "ko"));
  if (item.correspond_type_voyage === false) badges.append(badge("Hors type de voyage", "warn"));
  for (const activite of item.activites_correspondantes) badges.append(badge(`Activité : ${activite}`, "info"));

  const bottom = document.createElement("div");
  bottom.className = "offer-bottom";
  const price = document.createElement("div");
  price.className = "offer-price";
  price.textContent = `${item.prix_unitaire_eur} €`;
  const small = document.createElement("small");
  small.textContent = `par personne · ${item.prix_total_eur} € pour le groupe`;
  price.append(small);
  const updated = document.createElement("div");
  updated.className = "offer-updated";
  updated.textContent = `Mis à jour le ${formatDate(item.mis_a_jour_le)}`;
  bottom.append(price, updated);

  card.append(top, title, dest, desc, badges, bottom);
  return card;
}

function renderRecherche(recherche) {
  const container = $("#search-results");
  container.replaceChildren();

  const c = recherche.criteres;
  const source = document.createElement("div");
  source.className = "source-box";
  const lines = [
    `Source : ${recherche.source_label} (${recherche.source_url})`,
    `Prix et disponibilités récupérés le ${formatDate(recherche.consulte_le)}`,
    `Critères : ${c.destination} · départ ${c.date_depart}${c.date_retour ? ` · retour ${c.date_retour}` : ""} · ${c.participants} voyageur(s)` +
      `${c.budget_max ? ` · budget max ${c.budget_max} €/pers.` : ""}${c.type_voyage ? ` · ${TYPE_LABELS[c.type_voyage] || c.type_voyage}` : ""}` +
      `${c.activites.length ? ` · activités : ${c.activites.join(", ")}` : ""}`,
    `Disponibilité vérifiée à la date de départ (${c.date_verifiee}) uniquement.`,
  ];
  for (const line of lines) {
    const p = document.createElement("div");
    p.textContent = line;
    source.append(p);
  }
  container.append(source);

  const grid = document.createElement("div");
  grid.className = "catalogue-grid";
  if (!recherche.resultats.length) {
    const empty = document.createElement("div");
    empty.className = "demande-empty";
    empty.textContent = "Aucune prestation du catalogue pour cette destination.";
    grid.append(empty);
  } else {
    for (const item of recherche.resultats) grid.append(renderPrestation(item));
  }
  container.append(grid);
}

function appendBubble(role, content) {
  const bubble = document.createElement("div");
  bubble.className = `chat-bubble ${role}`;
  const p = document.createElement("p");
  p.textContent = content;
  bubble.append(p);
  const box = $("#chat-messages");
  box.append(bubble);
  box.scrollTop = box.scrollHeight;
}

async function sendMessage(text) {
  state.messages.push({ role: "user", content: text });
  appendBubble("user", text);
  $("#chat-status").hidden = false;
  $("#chat-error").textContent = "";
  try {
    const data = await api("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        messages: state.messages.slice(-50),
        ...(state.demandeId ? { demande_id: state.demandeId } : {}),
      }),
    });
    const reply = data.reply || "Je n'ai pas de réponse pour le moment.";
    state.messages.push({ role: "assistant", content: reply });
    appendBubble("assistant", reply);
    if (data.demande) renderRecap(data.demande);
    if (data.recherche) renderRecherche(data.recherche);
  } catch (err) {
    $("#chat-error").textContent = err.message;
  } finally {
    $("#chat-status").hidden = true;
  }
}

$("#chat-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const input = $("#chat-input");
  const text = input.value.trim();
  if (!text) return;
  input.value = "";
  sendMessage(text);
});

$("#reset-chat").addEventListener("click", () => {
  state.messages = [];
  state.demandeId = null;
  $("#chat-messages").replaceChildren();
  $("#recap-section").hidden = true;
  $("#search-section").hidden = true;
  $("#chat-error").textContent = "";
  appendBubble("assistant", WELCOME);
});

$("#search-button").addEventListener("click", async () => {
  if (!state.demandeId) return;
  const button = $("#search-button");
  $("#search-error").textContent = "";
  button.disabled = true;
  try {
    const data = await api(`/api/demandes/${encodeURIComponent(state.demandeId)}/recherche`, { method: "POST" });
    renderRecherche(data.recherche);
  } catch (err) {
    $("#search-results").replaceChildren();
    $("#search-error").textContent = err.message;
  } finally {
    button.disabled = false;
  }
});

/* ---------- Catalogue (lecture seule) ---------- */

function renderCatalogueItem(item) {
  const card = document.createElement("article");
  card.className = "offer-card";

  const top = document.createElement("div");
  top.className = "offer-card-top";
  const type = document.createElement("span");
  type.className = "offer-type";
  type.textContent = TYPE_PRESTATION_LABELS[item.type] || item.type;
  const id = document.createElement("span");
  id.className = "offer-id";
  id.textContent = item.id;
  top.append(type, id);

  const title = document.createElement("h3");
  title.textContent = item.nom;
  const dest = document.createElement("div");
  dest.className = "offer-destination";
  dest.textContent = item.destination;
  const desc = document.createElement("p");
  desc.textContent = item.description;

  const tags = document.createElement("div");
  tags.className = "badges";
  for (const tag of (item.tags || [])) tags.append(badge(`Tag : ${tag}`, "info"));

  const bottom = document.createElement("div");
  bottom.className = "offer-bottom";
  const price = document.createElement("div");
  price.className = "offer-price";
  price.textContent = `${item.prix_unitaire_eur} €`;
  const small = document.createElement("small");
  small.textContent = "prix de base / personne";
  price.append(small);
  bottom.append(price);

  card.append(top, title, dest, desc, tags, bottom);
  return card;
}

async function chargerCatalogue() {
  const grid = $("#catalogue-grid");
  if (!grid) return;
  grid.replaceChildren();
  $("#catalogue-error").textContent = "";
  try {
    const data = await api("/api/catalogue");
    const prestations = data.prestations || [];
    if (!prestations.length) {
      const vide = document.createElement("div");
      vide.className = "demande-empty";
      vide.textContent = "Aucune prestation dans le catalogue pour le moment.";
      grid.append(vide);
      return;
    }
    for (const item of prestations) grid.append(renderCatalogueItem(item));
  } catch (err) {
    $("#catalogue-error").textContent = err.message;
  }
}

/* ---------- Historique des conversations du voyageur ---------- */

function formatDateShort(iso) {
  const date = new Date(iso);
  return Number.isNaN(date.getTime())
    ? iso
    : date.toLocaleString("fr-FR", { dateStyle: "short", timeStyle: "short" });
}

async function chargerHistorique() {
  const liste = $("#history-list");
  if (!liste) return;
  liste.replaceChildren();
  try {
    const data = await api("/api/mes-demandes");
    const demandes = data.demandes || [];
    if (!demandes.length) {
      const vide = document.createElement("div");
      vide.className = "history-empty";
      vide.textContent = "Aucune conversation enregistrée. Décrivez votre voyage pour commencer.";
      liste.append(vide);
      return;
    }
    for (const demande of demandes) {
      const item = document.createElement("button");
      item.type = "button";
      item.className = "history-item"
        + (state.demandeId === demande.id ? " history-active" : "");
      const titre = document.createElement("span");
      titre.className = "history-item-titre";
      titre.textContent = `${demande.demande.destination} · ${demande.demande.date_depart}`;
      const meta = document.createElement("span");
      meta.className = "history-item-meta";
      meta.textContent = `${formatDateShort(demande.cree_le)} · ${demande.id}`;
      item.append(titre, meta);
      item.addEventListener("click", () => reprendreConversation(demande.id));
      liste.append(item);
    }
  } catch (err) {
    const erreur = document.createElement("div");
    erreur.className = "history-empty";
    erreur.textContent = err.message;
    liste.append(erreur);
  }
}

async function reprendreConversation(demId) {
  $("#chat-error").textContent = "";
  try {
    const data = await api(`/api/demandes/${encodeURIComponent(demId)}`);
    const record = data.demande;
    state.demandeId = record.id;
    state.messages = (record.messages || []).map((m) => ({ role: m.role, content: m.content }));
    const box = $("#chat-messages");
    box.replaceChildren();
    if (!state.messages.length) {
      appendBubble("assistant", WELCOME);
    } else {
      for (const m of state.messages) appendBubble(m.role, m.content);
    }
    renderRecap(record);
    const recherches = record.recherches || [];
    if (recherches.length) renderRecherche(recherches[recherches.length - 1]);
    else {
      $("#search-results").replaceChildren();
      $("#search-section").hidden = true;
    }
    $("#chat-messages").scrollTop = $("#chat-messages").scrollHeight;
    chargerHistorique();
  } catch (err) {
    $("#chat-error").textContent = err.message;
  }
}

appendBubble("assistant", WELCOME);
chargerHistorique();
chargerCatalogue();
