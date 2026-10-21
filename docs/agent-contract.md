# Agent contract

## Purpose

The DÉTOUR agent helps a travel advisor check fictional travel services and prepare a reliable response for a traveler.

The agent supports the advisor. It does not make a reservation and does not replace human approval.

## V1 scope

In V1, the agent can only:

- read a traveler request;
- identify missing information;
- consult the fictional DÉTOUR server;
- check the availability and price of a known service;
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
verifier_disponibilite(prestation_id, date, participants)
```

The tool checks the fictional price and availability of a service for a date and a number of participants.

The tool does not create an option and does not make a reservation.

## Tool arguments

### `prestation_id`

Rules:

- must be a known service identifier;
- must come from the fictional catalogue;
- must be a string;
- must not be invented by the model.

### `date`

Rules:

- must use the format `YYYY-MM-DD`;
- must be a valid calendar date;
- must be validated by the program before the server call.

### `participants`

Rules:

- must be an integer;
- must be between 1 and 100;
- must be validated by the program before the server call.

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

- use the tool when availability or price needs to be verified;
- ask a clarification question when a required argument is missing;
- state when a fact comes from the fictional server;
- mention the date, number of participants and service identifier used for the check;
- state when information is unavailable;
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
The fictional server confirms that train-nantes-01 is available
for 2 participants on 2026-11-07.

The verified total price is 96 EUR.

No option or reservation has been created.
```

## Error handling

The program must handle at least these cases:

| Situation | Expected behavior |
|---|---|
| Unknown tool | Reject the call and do not contact the server |
| Invalid service identifier | Return a validation error |
| Invalid date | Return a validation error |
| Invalid number of participants | Return a validation error |
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
choice on a changed line, and `decisions_statut` for the status decision.

The advisor name and the reason are mandatory. A status change that is not
allowed by the transition table is refused and nothing is written.

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

1. it asks for missing date or participant information instead of inventing it;
2. it calls only `verifier_disponibilite`;
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

## Open questions

- ? Should the agent receive the full traveler request or a structured object created by the application?
- ? Which model will be used for the demonstration?
- ? Who is allowed to expose the option and reservation tools in a later version?
- ? What information must appear in the proposal shown to the traveler?

Answered: the advisor's decision is stored in the append-only `decisions`
journal of the request and in the `decisions_statut` journal of the proposal,
with the author, the date and the reason.