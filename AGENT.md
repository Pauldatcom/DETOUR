# AGENT.md

Instructions for AI agents and other contributors working in this repository.
Read this file before making changes. The full contribution workflow is
described in [CONTRIBUTING.md](CONTRIBUTING.md).

## Project map

DÉTOUR is a course project built around a fictional travel agency. The
repository contains two applications, the AI agent contract and course
materials:

| Path | Role |
|---|---|
| `server/` | Fictional supplier API: catalogue, availability, options, simulated reservations. Read-only dashboard included. |
| `conseiller/` | Client-facing conversational application. A deterministic tool loop calls OpenRouter server-side and the supplier API server-side. |
| `conseiller/agent.py` | Conversational agent: the model proposes tool calls, the program validates and executes them. |
| `conseiller/propositions.py` | Proposition store (SQLite): CRUD, validation, status changes for travel proposals. |
| `conseiller/app.py` | Thin entrypoint: builds the stores and services into a `Context`, registers the routes and starts the stdlib HTTP server. |
| `conseiller/httpd/` | Generic HTTP plumbing: handler, router, sessions, access guards, errors and shared context. |
| `conseiller/routes/` | Business routes by domain (auth, account, demandes, propositions, chat, pages, stats, catalogue, meta). |
| `conseiller/static/` | Legacy portal assets served in non-built mode (`app.js`, `pages.js`, HTML and CSS). |
| `web/` | React/Vite front (TypeScript, Tailwind v4, React Router v7, Recharts). Dev: `pnpm dev` (:5173, proxy → :8766). Prod: `pnpm build` then the portal serves `web/dist`. |
| `observability/` | Grafana stack (docker-compose): Grafana, Prometheus, Loki, optional Alloy for Grafana Cloud. |
| `docs/agent-contract.md` | Contract of the DÉTOUR AI agent (V1 scope, tool, permissions, traces). Not a contribution guide. |
| `scripts/serve.py` | Static server for the slides. |

## Commands

From the repository root:

```
python3 server/app.py --demo        # supplier API + dashboard on http://127.0.0.1:8765
python3 conseiller/app.py           # client application on http://127.0.0.1:8766

cd web && pnpm install              # install front deps (first time)
cd web && pnpm dev                  # Vite dev server on http://localhost:5173 (proxy → :8766)
cd web && pnpm build                # build web/dist (served by the portal in prod)

cd observability && docker compose up -d   # Grafana (:3000), Prometheus (:9090), Loki (:3100)
cd observability && docker compose --profile cloud up -d alloy  # + push to Grafana Cloud

python3 scripts/serve.py            # slides on http://127.0.0.1:8000
```

Tests:

```
python3 -m unittest discover -s server/tests -v          # 20 tests
python3 -m unittest discover -s conseiller/tests -v      # 485 tests
cd web && pnpm tsc --noEmit          # TypeScript typecheck
cd web && pnpm build                 # Vite build (fails on type errors)
cd web && pnpm lint                  # ESLint
cd web && pnpm format:check          # Prettier check
```

Lint and format the front (both write in place):

```
cd web && pnpm lint:fix
cd web && pnpm format
```

Continuous integration: `.github/workflows/test.yml` runs on every pull
request (tests on Python 3.13, lint, build). The workflow is a
required status check on `main`.

A pre-commit hook (`web/.husky/pre-commit`, wired via `husky` +
`lint-staged`) runs `prettier --write` and `eslint --fix` on staged
front files. It is installed automatically by `pnpm install` (the
`prepare` script). `format:check` stays in CI as a safety net.

The supplier server must run before the client application can search
prestations.

## Conventions

- Python standard library only. Do not add dependencies. The `web/`
  directory is an exception: it is a React/Vite front managed by `pnpm`
  and is not subject to the stdlib-only rule. The Python backend
  (`conseiller/`, `server/`) must remain stdlib-only.
- Server-side code holds the credentials. `X-Team-Key` (`TRAVEL_TEAM_KEY`)
  and `OPENROUTER_API_KEY` stay in environment variables or `.env`
  (see `.env.example`); they are never sent to the browser, never logged,
  never stored in traces, never exposed to the model.
- Google OAuth credentials (`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`)
  follow the same rule. The `web/` front only uses `VITE_`-prefixed
  variables (public by design).
- The supplier API is a shared constraint: extend it additively and keep its
  documented contract (`server/README.md`, `server/CONTRAT.md`) accurate.
- User-facing texts of the applications are in French.
- Code comments are in English only. No French comments in source code.
- Never simulate a success: if the supplier is unreachable, report the error.
- New API routes go in the matching module under `conseiller/routes/` and are
  registered from `routes/__init__.py`. Access rules live in
  `httpd/gardes.py`; generic HTTP plumbing belongs in `httpd/`.

## AI agent work

When working on the DÉTOUR agent, follow [docs/agent-contract.md](docs/agent-contract.md):
the model proposes, the program validates and executes, the advisor decides.
Never expose `X-Team-Key`, `X-Approval-Key` or OpenRouter credentials to the
model, to logs or to traces.

## Contribution rules (summary)

- Every change is linked to a GitHub Issue.
- Branches: `<type>/<issue-number>-<short-description>` with types `feat`,
  `fix`, `docs`, `refactor`, `test`, `chore`, `build`, `ci`, `perf`, `revert`.
- Commits: `type(scope): imperative summary`.
- Pull requests: Conventional Commit title, English description, reference
  the issue with `Closes #123`, `Fixes #123` or `Refs #123`.
- `main` is protected: one approving review, no direct pushes, no force
  pushes, administrators included.
- No feature is delivered without an associated unit test.