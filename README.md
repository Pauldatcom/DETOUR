# DÉTOUR — Agence de voyages insolites

Projet pédagogique : application conseiller + voyageur pour une agence de
voyages fictive. Backend Python stdlib (sans dépendances), front React/Vite,
observabilité Grafana.

## Démarrage rapide

```bash
# 1. Backend Python (supplier + portail)
python3 server/app.py --demo        # :8765 — API prestations fictives
python3 conseiller/app.py           # :8766 — portail conseiller/voyageur

# 2. Front React (dev)
cd web
pnpm install
pnpm dev                             # :5173 (proxy → :8766)

# 3. Observabilité (optionnel)
cd observability
cp .env.example .env                 # renseigner GRAFANA_CLOUD_* si push Cloud
docker compose up -d                 # Grafana :3000, Prometheus :9090, Loki :3100
```

Ouvrir `http://localhost:5173` en dev, `http://127.0.0.1:8766` en prod
(une fois `pnpm build` exécuté dans `web/`).

## Configuration

Copiez `.env.example` en `.env` à la racine :

| Variable | Rôle |
|---|---|
| `OPENROUTER_API_KEY` | Clé OpenRouter pour l'agent conversationnel |
| `OPENROUTER_MODEL` | Modèle (défaut : `openai/gpt-4o-mini`) |
| `TRAVEL_TEAM_KEY` | Clé d'équipe pour le supplier (démo : `demo-key`) |
| `TRAVEL_API_URL` | URL du supplier (défaut : `http://127.0.0.1:8765`) |
| `GOOGLE_CLIENT_ID` | OAuth Google (optionnel) |
| `GOOGLE_CLIENT_SECRET` | OAuth Google (optionnel) |
| `GOOGLE_REDIRECT_URI` | `http://localhost:8766/api/auth/google/callback` |
| `METRICS_TOKEN` | Token d'accès `/metrics` (optionnel) |

## Architecture

```
server/          Supplier API (catalogue, recherche, dashboard) — :8765
conseiller/       Portail (auth, chat, demandes, propositions, OAuth, /metrics) — :8766
  app.py          Serveur HTTP stdlib, routes API, sert web/dist en prod
  agent.py        Agent OpenRouter (tool-calling, génération de propositions)
  propositions.py Store JSON des propositions (CRUD, statuts)
  users.py         Comptes voyageurs (PBKDF2) + Google OAuth
  store.py         Store JSON des demandes
  fournisseur.py   Client du supplier API
web/              Front React (Vite + TS + Tailwind v4 + RR v7 + Recharts)
  src/pages/       Login, Dashboard, Demandes, Propositions, MesPropositions
  src/components/  Header, Sidebar, StatsCard, DataTable, PropositionCard…
observability/    Grafana + Prometheus + Loki (+ Alloy pour Grafana Cloud)
```

## Routes API

| Route | Méthode | Accès | Description |
|---|---|---|---|
| `/api/config` | GET | public | Feature flags |
| `/api/session` | GET | public | Session courante |
| `/api/login` | POST | public | Connexion voyageur |
| `/api/register` | POST | public | Inscription voyageur |
| `/api/login-conseiller` | POST | public | Connexion conseiller (clé) |
| `/api/auth/google` | GET | public | OAuth Google (PKCE) |
| `/api/auth/google/callback` | GET | public | Callback OAuth |
| `/api/demandes` | GET | conseiller | Liste demandes |
| `/api/demandes` | POST | client | Créer demande |
| `/api/demandes/{id}` | GET | conseiller/propriétaire | Détail |
| `/api/demandes/{id}/recherche` | POST | conseiller/propriétaire | Recherche supplier |
| `/api/demandes/{id}/statut` | PATCH | conseiller | Changer statut |
| `/api/demandes/{id}/propositions` | POST | conseiller | Créer proposition |
| `/api/demandes/{id}/propositions/generer` | POST | conseiller | Générer via IA |
| `/api/propositions` | GET | conseiller | Liste propositions |
| `/api/propositions/{id}` | GET | conseiller/propriétaire | Détail |
| `/api/propositions/{id}` | PATCH | conseiller | Modifier |
| `/api/propositions/{id}/statut` | PATCH | conseiller | Statut |
| `/api/mes-demandes` | GET | client | Mes demandes |
| `/api/mes-propositions` | GET | client | Mes propositions |
| `/api/stats` | GET | conseiller | Statistiques |
| `/api/catalogue` | GET | client | Catalogue supplier |
| `/api/chat` | POST | client | Chat agent |
| `/metrics` | GET | public/token | Prometheus |

## Tests

```bash
python3 -m unittest discover -s server/tests -v
python3 -m unittest discover -s conseiller/tests -v    # 85 tests
cd web && pnpm tsc --noEmit                              # typecheck TS
cd web && pnpm build                                     # build (échec si erreur TS)
```

## Contribution

Voir [CONTRIBUTING.md](CONTRIBUTING.md) et [AGENT.md](AGENT.md).
Branches : `<type>/<issue>-<short>`. Commits : `type(scope): summary`.