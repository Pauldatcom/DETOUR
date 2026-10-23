# DÉTOUR — Unusual travel agency

Educational project: advisor + traveler application for a fictional travel
agency. Python stdlib backend (no dependencies), React/Vite front end,
Grafana observability.

## Quick start

```bash
# Prerequisites: Docker Desktop (or Docker Engine + Compose)

# 1. React front (dev — builds + starts the full Docker stack)
cd web
pnpm install
pnpm dev                             # supplier :8765 · portail :8766 · Grafana :3000 · Vite :5173

# 2. Manual Docker control (from repo root)
docker compose up -d                 # start all backend + observability containers
docker compose down                  # stop them
```

`pnpm dev` requires Docker. If Docker is unavailable, fall back to the
Python servers directly:

```bash
python3 server/app.py --demo         # :8765 — fictional services API
python3 conseiller/app.py            # :8766 — advisor/traveler portal
cd web && pnpm dev                   # :5173 (proxy → :8766, Vite only)
```

Open `http://localhost:5173` in dev, `http://127.0.0.1:8766` in prod
(once `pnpm build` has run in `web/`).

## Configuration

Copy `.env.example` to `.env` at the repository root:

| Variable | Purpose |
|---|---|
| `OPENROUTER_API_KEY` | OpenRouter key for the conversational agent |
| `OPENROUTER_MODEL` | Model (default: `nvidia/nemotron-3.5-super-vl:free`, free) |
| `TRAVEL_TEAM_KEY` | Team key for the supplier (demo: `demo-key`) |
| `TRAVEL_API_URL` | Supplier URL (default: `http://127.0.0.1:8765`) |
| `GOOGLE_CLIENT_ID` | Google OAuth (optional) |
| `GOOGLE_CLIENT_SECRET` | Google OAuth (optional) |
| `GOOGLE_REDIRECT_URI` | `http://localhost:8766/api/auth/google/callback` |
| `METRICS_TOKEN` | Access token for `/metrics` (optional) |

## Architecture

```
server/           Supplier API (catalogue, search, dashboard) — :8765
  Dockerfile      python:3.13-slim, no pip deps (stdlib-only rule)
conseiller/        Portal (auth, chat, demandes, propositions, OAuth, /metrics) — :8766
  app.py           Stdlib HTTP server, API routes, serves web/dist in prod
  agent.py         OpenRouter agent (tool-calling, proposition generation)
  propositions.py  SQLite store for propositions (CRUD, statuses)
  users.py          Traveler accounts (PBKDF2) + Google OAuth
  store.py          SQLite store for demandes
  fournisseur.py    Supplier API client
  Dockerfile        python:3.13-slim, no pip deps (stdlib-only rule)
web/               React front (Vite + TS + Tailwind v4 + RR v7 + Recharts)
  src/pages/        Login, Dashboard, Demandes, Propositions, MesPropositions
  src/components/   Header, Sidebar, StatsCard, DataTable, PropositionCard…
  scripts/dev.mjs   pnpm dev orchestrator: Docker stack → health checks → Vite
observability/     Grafana + Prometheus + Loki (+ Alloy for Grafana Cloud)
docker-compose.yml Root compose: include observability + fournisseur + portail
```

## API routes

| Route | Method | Access | Description |
|---|---|---|---|
| `/api/config` | GET | public | Feature flags |
| `/api/session` | GET | public | Current session |
| `/api/login` | POST | public | Traveler login |
| `/api/register` | POST | public | Traveler registration |
| `/api/login-conseiller` | POST | public | Advisor login (team key + first name, which signs proposals) |
| `/api/auth/google` | GET | public | Google OAuth (PKCE) |
| `/api/auth/google/callback` | GET | public | OAuth callback |
| `/api/demandes` | GET | advisor | List demandes |
| `/api/demandes` | POST | client | Create demande |
| `/api/demandes/{id}` | GET | advisor/owner | Detail |
| `/api/demandes/{id}/recherche` | POST | advisor/owner | Supplier search |
| `/api/demandes/{id}/statut` | PATCH | advisor | Change status |
| `/api/demandes/{id}/reponse` | POST | advisor | Send the response to a request (status `repondue`, response time vs 24h / 48h) |
| `/api/demandes/{id}/propositions` | POST | advisor | Create proposition |
| `/api/demandes/{id}/propositions/generer` | POST | advisor | Generate via AI |
| `/api/propositions` | GET | advisor | List propositions |
| `/api/propositions/{id}` | GET | advisor/owner | Detail |
| `/api/propositions/{id}` | PATCH | advisor | Update |
| `/api/propositions/{id}/statut` | PATCH | advisor | Status |
| `/api/propositions/{id}/accepter` | POST | advisor | Accept a proposal |
| `/api/propositions/{id}/correction` | POST | advisor | Request a correction (reason + instructions) |
| `/api/propositions/{id}/refuser` | POST | advisor | Reject a proposal (reason) |
| `/api/mes-demandes` | GET | client | My demandes |
| `/api/mes-propositions` | GET | client | My propositions (only those sent by an advisor, never drafts) |
| `/api/stats` | GET | advisor | Statistics |
| `/api/catalogue` | GET | client | Supplier catalogue |
| `/api/chat` | POST | client | Agent chat |
| `/metrics` | GET | public/token | Prometheus |

## Tests

```bash
python3 -m unittest discover -s server/tests -v          # 17 tests
python3 -m unittest discover -s conseiller/tests -v      # 230 tests
cd web && pnpm tsc --noEmit                              # TS typecheck
cd web && pnpm build                                     # build (fails on TS errors)
cd web && pnpm lint                                      # ESLint
cd web && pnpm format:check                              # Prettier
```

## Continuous integration

`.github/workflows/test.yml` runs on every pull request:

| Job | What it checks |
|---|---|
| `Tests (Python 3.13)` | the two `unittest` suites, standard library only |
| `Lint` | Prettier formatting, ESLint, TypeScript typecheck |
| `Build` | the React production build |
| `Security Audit` | `pnpm audit --audit-level=high`, never blocking |

The workflow is a required status check on `main`: a pull request cannot be
merged while a job fails.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and [AGENT.md](AGENT.md).
Branches: `<type>/<issue>-<short>`. Commits: `type(scope): summary`.
