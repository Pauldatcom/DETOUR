"use strict";

const $ = (selector) => document.querySelector(selector);
const state = { catalogue: [], json: null };
const labels = { transport: "Transport", hebergement: "Hébergement", activite: "Activité" };

function el(tag, className, content) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (content !== undefined) node.textContent = content;
  return node;
}

async function request(path, options = {}) {
  const response = await fetch(path, { credentials: "same-origin", cache: "no-store", ...options });
  const data = await response.json();
  if (!response.ok) {
    if (response.status === 401 && path !== "/dashboard/api/login") showLogin();
    throw new Error(data.erreur?.message || "Le serveur ne répond pas.");
  }
  return data;
}

function showLogin() {
  $("#login-screen").hidden = false;
  $("#dashboard").hidden = true;
  $("#team-name").hidden = true;
  $("#logout").hidden = true;
}

function showDashboard(team) {
  $("#login-screen").hidden = true;
  $("#dashboard").hidden = false;
  $("#team-name").textContent = team;
  $("#team-name").hidden = false;
  $("#logout").hidden = false;
}

function showJSON(payload, source) {
  state.json = JSON.stringify(payload, null, 2);
  $("#response-json").textContent = state.json;
  $("#response-source").textContent = source;
  $("#copy-json").disabled = false;
  $("#response-panel").scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function tomorrow() {
  const day = new Date();
  day.setDate(day.getDate() + 1);
  return `${day.getFullYear()}-${String(day.getMonth() + 1).padStart(2, "0")}-${String(day.getDate()).padStart(2, "0")}`;
}

function renderCatalogue() {
  const destination = $("#destination").value;
  const type = $("#type").value;
  const items = state.catalogue.filter((item) => (!destination || item.destination === destination) && (!type || item.type === type));
  $("#catalogue-count").textContent = String(items.length).padStart(2, "0");
  const grid = $("#catalogue-grid");
  grid.replaceChildren();
  if (!items.length) {
    grid.append(el("div", "empty-state", "Aucune prestation pour cette sélection."));
    return;
  }
  for (const item of items) {
    const card = el("article", "offer-card");
    const top = el("div", "offer-card-top");
    top.append(el("span", "offer-type", labels[item.type] || item.type), el("span", "offer-id", item.id));
    card.append(top, el("h3", "", item.nom), el("div", "offer-destination", item.destination), el("p", "", item.description));
    const bottom = el("div", "offer-bottom");
    const price = el("div", "offer-price", `${item.prix_unitaire_eur} €`);
    price.append(el("small", "", "prix de base / personne"));
    const actions = el("div", "offer-actions");
    const inspect = el("button", "icon-button", "JSON");
    inspect.type = "button";
    inspect.setAttribute("aria-label", `Voir le JSON de ${item.nom}`);
    inspect.addEventListener("click", async () => {
      try {
        $("#catalogue-error").textContent = "";
        const payload = await request(`/dashboard/api/prestations/${encodeURIComponent(item.id)}`);
        showJSON(payload, `GET /api/v1/prestations/${item.id}`);
      } catch (error) { $("#catalogue-error").textContent = error.message; }
    });
    const check = el("button", "icon-button check-button", "Vérifier");
    check.type = "button";
    check.setAttribute("aria-label", `Vérifier la disponibilité de ${item.nom}`);
    check.addEventListener("click", () => checkAvailability(item));
    actions.append(inspect, check);
    bottom.append(price, actions);
    card.append(bottom);
    grid.append(card);
  }
}

async function checkAvailability(item) {
  const onDate = $("#travel-date").value;
  const participants = Number($("#participants").value);
  if (!onDate || !Number.isInteger(participants) || participants < 1 || participants > 20) {
    $("#catalogue-error").textContent = "Choisissez une date et entre 1 et 20 participants.";
    return;
  }
  $("#catalogue-error").textContent = "";
  const query = new URLSearchParams({ prestation_id: item.id, date: onDate, participants: String(participants) });
  try {
    const payload = await request(`/dashboard/api/disponibilites?${query}`);
    showJSON(payload, `GET /api/v1/disponibilites?${query}`);
  } catch (error) { $("#catalogue-error").textContent = error.message; }
}

function renderRecords(container, records, kind) {
  container.replaceChildren();
  if (!records.length) {
    container.append(el("div", "empty-list", kind === "option" ? "Aucune option posée pour votre équipe." : "Aucune réservation confirmée pour votre équipe."));
    return;
  }
  for (const record of records) {
    const card = el("article", "record");
    const top = el("div", "record-top");
    const title = state.catalogue.find((item) => item.id === record.prestation_id)?.nom || record.prestation_id;
    top.append(el("strong", "", title), el("span", `status${["active", "confirmee"].includes(record.statut) ? "" : " inactive"}`, record.statut));
    card.append(top, el("div", "record-meta", `${record.date} · ${record.participants} participant${record.participants > 1 ? "s" : ""} · ${record.prix_total_eur} €`), el("div", "record-id", record.id));
    const inspect = el("button", "icon-button", "Voir le JSON");
    inspect.type = "button";
    inspect.addEventListener("click", () => showJSON({ [kind]: record, simulation: true }, `GET /api/v1/${kind === "option" ? "options" : "reservations"}`));
    card.append(inspect);
    container.append(card);
  }
}

async function loadSpace() {
  $("#space-error").textContent = "";
  try {
    const [options, reservations] = await Promise.all([request("/dashboard/api/options"), request("/dashboard/api/reservations")]);
    $("#options-count").textContent = String(options.options.length);
    $("#reservations-count").textContent = String(reservations.reservations.length);
    $("#space-count").textContent = String(options.options.length + reservations.reservations.length).padStart(2, "0");
    renderRecords($("#options-list"), options.options, "option");
    renderRecords($("#reservations-list"), reservations.reservations, "reservation");
  } catch (error) { $("#space-error").textContent = error.message; }
}

async function loadDashboard() {
  const catalogue = await request("/dashboard/api/catalogue");
  state.catalogue = catalogue.prestations;
  const cities = [...new Set(state.catalogue.map((item) => item.destination))].sort((a, b) => a.localeCompare(b, "fr"));
  const allCities = el("option", "", "Toutes");
  allCities.value = "";
  $("#destination").replaceChildren(allCities);
  for (const city of cities) {
    const option = el("option", "", city);
    option.value = city;
    $("#destination").append(option);
  }
  renderCatalogue();
  await loadSpace();
}

$("#travel-date").value = tomorrow();
$("#login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  $("#login-error").textContent = "";
  const input = $("#team-key");
  const teamKey = input.value;
  input.value = "";
  try {
    const data = await request("/dashboard/api/login", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ team_key: teamKey }) });
    showDashboard(data.equipe);
    await loadDashboard();
  } catch (error) { $("#login-error").textContent = error.message; }
});

$("#logout").addEventListener("click", async () => {
  try { await request("/dashboard/api/logout", { method: "POST" }); } catch { /* Clear the visible session even if the server is unavailable. */ }
  state.catalogue = [];
  state.json = null;
  $("#response-json").textContent = "{}";
  $("#copy-json").disabled = true;
  showLogin();
});

for (const selector of ["#destination", "#type"]) $(selector).addEventListener("change", renderCatalogue);
$("#refresh-space").addEventListener("click", loadSpace);
$("#copy-json").addEventListener("click", async () => {
  if (!state.json) return;
  try {
    await navigator.clipboard.writeText(state.json);
    $("#copy-feedback").textContent = "JSON copié.";
    $("#copy-json").textContent = "Copié ✓";
    setTimeout(() => { $("#copy-json").textContent = "Copier le JSON"; }, 1800);
  } catch { $("#copy-feedback").textContent = "Copie impossible. Sélectionnez le JSON affiché."; }
});

for (const button of document.querySelectorAll(".tab")) {
  button.addEventListener("click", () => {
    for (const tab of document.querySelectorAll(".tab")) {
      tab.classList.toggle("active", tab === button);
      if (tab === button) tab.setAttribute("aria-current", "page"); else tab.removeAttribute("aria-current");
    }
    const isCatalogue = button.dataset.view === "catalogue";
    $("#catalogue-view").hidden = !isCatalogue;
    $("#espace-view").hidden = isCatalogue;
    if (!isCatalogue) loadSpace();
  });
}

request("/dashboard/api/me").then((data) => {
  showDashboard(data.equipe);
  return loadDashboard();
}).catch(() => showLogin());
