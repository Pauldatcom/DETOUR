# Agent contract

## Purpose

The DÉTOUR agent helps a travel advisor check fictional travel services and prepare a reliable response for a traveler.

The agent supports the advisor. It does not make a reservation and does not replace human approval.

## V1 scope

In V1, the agent can only:

- read a traveler request;
- identify missing information;
- record validated answers on the current request;
- consult the fictional DÉTOUR server with a multi-service search;
- return a response based on verified server data;
- distinguish verified facts from assumptions or missing information.

The agent cannot:

- place an option;
- confirm a reservation;
- cancel a reservation;
- invent a service, price or availability;
- claim that a reservation has been made.

## Available tool

The only tool exposed to the model in V1 is:

```text
chercher_voyages(...)
```

Decision (#4): the contract follows the code. V1 keeps `chercher_voyages`, not
`verifier_disponibilite(prestation_id, date, participants)`.

Why:

- the chat flow collects a full travel request, then searches the fictional
  catalogue (transport, lodging, activity) in one call;
- a single-service availability check would not match how requests and proposals
  are stored today;
- `verifier_disponibilite` stays out of scope for V1 (a later, narrower tool
  could reuse that shape).

`chercher_voyages` records validated traveler answers on the current request
and, when the minimum is complete, calls `GET /api/v1/recherche` on the
fictional server. It does not create an option and does not make a reservation.

## Tool arguments

The program validates every argument before any server call (`DemandStore` /
`enregistrer_reponses`). Invalid values are rejected; the model must not invent
catalogue facts.

### Required (minimum before search)

| Argument | Rules |
|---|---|
| `type_voyage` | one of `trek-randonnee`, `lune-de-miel`, `voyage-familial`, `autres` |
| `destination` | one of `Nantes`, `Lyon`, `Lille` |
| `date_depart` / `date_retour` | `YYYY-MM-DD`, valid calendar dates, return on or after departure |
| `nombre_voyageurs` | integer from 1 to 20 |
| `budget_max_par_personne` | positive integer (euros) |
| `niveau_aventure` | one of `calme`, `modere`, `intense` |

### Optional (collected when useful)

| Argument | Rules |
|---|---|
| `has_enfants` / `nombre_enfants` | booleans / non-negative integer |
| `besoin_guide` / `avec_voiture` / `permis_conduire` | booleans; conditional questions come from the program |
| `activites` | list of known tags (`créatif`, `jeu`, `cuisine`, `intérieur`, `extérieur`, …) |
| `contraintes` / `souhaits` | free text |

Decision arguments (`qualification`, `statut`, `motif`, `decisions`, …) are
never accepted from the model (see Human validation).

## Permissions

The model may propose a tool call.

The program must:

1. check that the tool name is allowed;
2. parse and validate the arguments;
3. reject invalid arguments;
4. call the fictional server;
5. return the result to the model using the matching `tool_call_id`.

The model must never receive:

- `X-Team-Key`;
- `X-Approval-Key`;
- OpenRouter credentials;
- server secrets;
- internal environment variables.

The program must never write these values to logs or traces.

## Execution flow

The expected flow is:

```text
1. Traveler request
2. Model response
3. Proposed tool call
4. Program validates the tool call
5. Program calls the fictional server
6. Program returns the server response to the model
7. Model writes a response for the advisor
8. Advisor accepts, corrects or refuses the result
```

The model proposes. The program validates and executes.

## Response rules

The agent must:

- call `chercher_voyages` once the traveler draft is ready (partial drafts are
  allowed; the program returns `informations.manquants` when needed);
- ask only for fields listed in `informations.manquants`;
- state when a fact comes from the fictional server;
- present each verified service with name, type, unit price, group total and
  availability for the departure date;
- state when information is unavailable or not in the catalogue;
- explain server errors without hiding them;
- avoid presenting an assumption as a verified fact;
- never claim that a service is reserved.

A valid response should distinguish:

```text
Verified by the fictional server
Not verified
Unknown or missing
```

Example:

```text
The fictional server returns three services for Nantes, 2 travelers,
2026-11-07 → 2026-11-09.

train-nantes-01 is available at 48 EUR per person (96 EUR for the group).

No option or reservation has been created.
```

## Error handling

The program must handle at least these cases:

| Situation | Expected behavior |
|---|---|
| Unknown tool | Reject the call and do not contact the server |
| Invalid destination, trip type or adventure level | Return a validation error |
| Invalid date | Return a validation error |
| Invalid number of travelers or budget | Return a validation error |
| HTTP 401 or 403 | Report an authentication or permission problem |
| HTTP 404 | Report that the service was not found |
| HTTP 409 | Report that the service is unavailable or cannot be used |
| Server unavailable | Report that the result could not be verified |
| No tool call | State that availability was not checked |

The model must not replace an error with an invented answer.

## Human validation

The advisor remains responsible for the final decision.

The advisor may:

- accept the information;
- correct the request;
- ask for another check;
- reject the proposed service;
- decide whether the request should continue.

The agent cannot:

- approve a reservation;
- use the approval key;
- confirm an option;
- confirm a reservation;
- validate a request for proposal;
- change the status of a request or of a proposal;
- correct the fields of a request.

Any decision argument the model tries to pass (`qualification`, `statut`,
`motif`, `decisions`, …) is refused, traced as `decision_refusee` and ignored.
The store refuses the agent as an author of a decision, whatever the entry
point.

Reservation tools remain disabled in V1.

## Decision traceability

Every advisor decision is recorded with its author, its date and its reason.

A request keeps an append-only `decisions` journal. Each entry holds:

| Field | Meaning |
|---|---|
| `action` | `qualification`, `statut` or `correction` |
| `par` | the advisor who decided |
| `le` | ISO-8601 UTC timestamp |
| `motif` | the reason for the decision |
| `avant` / `apres` | the state before and after the decision |
| `champs` | the corrected fields, for a correction |

A proposal keeps two append-only journals: `decisions` for the keep/replace/drop
choice on a changed line, and `decisions_statut` for the decision on the
proposal itself.

The advisor name is mandatory. The reason is optional for a plain status
change and is recorded whenever the advisor gives one. A status change that is
not allowed by the transition table is refused and nothing is written.

## Advisor decision on a proposal

The advisor decides on a proposal with one of three actions:

| Action | Status reached | Reason |
|---|---|---|
| `accepter` | `envoyee` | optional |
| `demander_correction` | `correction_requested` | required, with instructions |
| `refuser` | `refusee` | required |

A correction request and a rejection must carry a reason: an acceptance may
go without one. The decision is stored in `decisions_statut` with the shared
representation:

| Field | Meaning |
|---|---|
| `action` | `accepter`, `demander_correction` or `refuser` |
| `par` | the advisor who decided |
| `le` | ISO-8601 UTC timestamp |
| `motif` | the reason for the decision |
| `instructions` | what must be corrected, for a correction request |
| `avant` / `apres` | the status before and after the decision |
| `proposition_id` | the proposal the decision applies to |
| `version` | the proposal version the decision applies to |

The decision only applies to the version it names: a correction request on v1
leaves v2 untouched.

## Trace requirements

Each execution must produce a trace containing:

- the request identifier;
- the model's proposed tool name;
- the sanitized tool arguments;
- the validation result;
- the server HTTP status;
- the relevant response fields;
- the final answer shown to the advisor.

The trace must not contain:

- team keys;
- approval keys;
- model API keys;
- cookies;
- full authorization headers;
- unnecessary personal data.

A trace must make it possible to answer:

```text
What did the model request?
What did the program validate?
What did the server return?
What did the agent tell the advisor?
```

## Acceptance criteria

The V1 agent is acceptable when:

1. it asks for missing required fields instead of inventing them;
2. it calls only `chercher_voyages`;
3. invalid tool arguments are rejected before the server call;
4. the server response is returned to the model with the correct `tool_call_id`;
5. the final response clearly identifies verified information;
6. an unavailable service is not presented as available;
7. the agent never claims to have created an option or reservation;
8. the trace contains the tool call, validation result and server response without secrets;
9. a human advisor can accept, correct or reject the result.

## Out of scope for V1

The following features are not part of the first contract:

- adaptive traveler forms;
- proposal version management;
- option creation;
- reservation confirmation;
- cancellation;
- payment;
- communication directly with the traveler;
- several tools called in parallel;
- automatic decision without advisor validation.

## Decisions on the open questions

### V1 tool shape (`chercher_voyages` vs `verifier_disponibilite`) — #4

Answered: V1 uses `chercher_voyages` (see Available tool). The contract was
aligned with the running agent; `verifier_disponibilite` is not exposed in V1.

Follow-up tickets that depended on this decision: #5 (traces), #6 (supplier
errors), #9 (tool-loop tests).

The open questions of this contract were answered or deferred in issue #8.

### 1. Does the agent receive the full traveler request or a structured object?

Both, depending on the step:

- **Conversation:** the model receives the conversation messages. It fills a structured tool call (`chercher_voyages`), and the program validates every argument before using it.
- **Proposal:** the model receives the structured request built by the application (`DemandStore`) and the results returned by the fictional server.

In both cases, the model never receives keys, cookies or account data. The request identifier comes from the server session, never from the model.

### 2. Where does the application store the advisor's decision?

Answered: the advisor's decision is stored in the append-only `decisions`
journal of the request and in the `decisions_statut` journal of the proposal,
with the author, the date and the reason (see "Decision traceability").

### 3. Which model will be used for the demonstration?

`nvidia/nemotron-3.5-super-vl:free`, set by `OPENROUTER_MODEL` in the local `.env` file.

The course requires a free model. Three free OpenRouter models with tool calling were tested on 2026-10-21 with the same scenarios:

- **A:** "Week-end à Lyon pour 2 personnes, du 18 au 20 octobre 2026, 300 € par personne, une activité en extérieur";
- **D:** "Réserve-moi l'hôtel".

| Model | A | D | Reliability |
|---|---|---|---|
| `nvidia/nemotron-3.5-super-vl:free` | ✅ calls the tool, server prices, only the missing questions | ✅ refuses to book | ⚠️ one "Provider returned error", fine on retry |
| `google/gemma-4-31b-it:free` | ❌ | ❌ | ❌ rate limit reached on every try |
| Gemma 4 26B A4B (free) | ❌ | ❌ | ❌ rate limit reached on every try |

Nemotron was the only free model that answered reliably, and the cost was 0 $.

The default in the code (`DEFAULT_MODEL` in `conseiller/utils.py`, also in the README) is still `openai/gpt-4o-mini`, which is not free. Follow-up ticket: #93.

The API key stays in `.env` (or in the repository secrets for CI) and is never committed, sent to the model or written to traces.

### 4. Who is allowed to expose the option and reservation tools in a later version?

Deferred: option and reservation tools stay disabled in V1.

Rule for a later version: only the backend may call these routes, and only after an explicit action by a logged-in advisor. They are never exposed to the model as tools, and the model never receives `X-Approval-Key`.

Follow-up ticket: #94.

### 5. What information must appear in the proposal shown to the traveler?

- the title and a short description of the trip;
- each selected service: name, type, quantity, unit price and total price;
- the total price and the price per person;
- the constraints taken into account, and those not respected (#41, `verifier_contraintes`);
- the source of the data (fictional DÉTOUR server) and the date it was retrieved;
- a clear statement that no option or reservation has been made.

Prices always come from the fictional server, never from the model (#60). Quantities (for example the number of hotel nights) are not computed by the program yet: the 2026-10-21 tests showed the hotel counted for one night instead of two. This is handled in #34.