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
| `docs/agent-contract.md` | Contract of the DÉTOUR AI agent (V1 scope, tool, permissions, traces). Not a contribution guide. |
| `content/`, `slides/`, `output/` | Course materials (briefs, exercises, slides, PDFs). |
| `scripts/serve.py` | Static server for the slides. |

## Commands

From the repository root:

```
python3 server/app.py --demo        # supplier API + dashboard on http://127.0.0.1:8765
python3 conseiller/app.py           # client application on http://127.0.0.1:8766
python3 scripts/serve.py            # slides on http://127.0.0.1:8000
```

Tests:

```
python3 -m unittest discover -s server/tests -v
python3 -m unittest discover -s conseiller/tests -v
```

The supplier server must run before the client application can search
prestations.

## Conventions

- Python standard library only. Do not add dependencies.
- Server-side code holds the credentials. `X-Team-Key` (`TRAVEL_TEAM_KEY`)
  and `OPENROUTER_API_KEY` stay in environment variables or `.env`
  (see `.env.example`); they are never sent to the browser, never logged,
  never stored in traces, never exposed to the model.
- The supplier API is a shared constraint: extend it additively and keep its
  documented contract (`server/README.md`, `server/CONTRAT.md`) accurate.
- User-facing texts of the applications are in French.
- Code comments are in English only. No French comments in source code.
- Never simulate a success: if the supplier is unreachable, report the error.

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