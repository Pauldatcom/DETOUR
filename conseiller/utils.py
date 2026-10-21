"""Définitions globales de l'application conseiller DÉTOUR.

Ce module centralise les constantes partagées (contrat métier, limites,
identifiants d'outils) pour qu'elles restent visibles dans le dépôt.
Les valeurs secrètes ou déployables (clés, URL effectives, modèle choisi)
restent dans l'environnement ou `.env`, jamais ici.
"""

import re

# Fournisseur de prestations (surchargeable par TRAVEL_API_URL).
DEFAULT_URL = "http://127.0.0.1:8765"
SOURCE_LABEL = "Serveur fictif DÉTOUR"

# Agent conversationnel (surchargeable par OPENROUTER_MODEL).
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-4o-mini"
MAX_MESSAGES = 40
MAX_TOOL_ITERATIONS = 3
TOOL_NAME = "chercher_voyages"

# Contrat métier partagé avec le serveur fictif.
TYPES_VOYAGE = ("trek-randonnee", "lune-de-miel", "voyage-familial", "autres")
NIVEAUX_AVENTURE = ("calme", "modere", "intense")
ACTIVITES_POSSIBLES = ("créatif", "jeu", "cuisine", "intérieur", "extérieur", "train", "sans voiture")

# Statuts d'une demande.
STATUT_NOUVELLE = "nouvelle"
STATUT_A_ANALYSER = "a_analyser"
STATUT_A_REVOIR = "a_revoir"  # To review — price or availability changed after v1.
STATUT_PROPOSE = "propose"
STATUT_VALIDE = "valide"
STATUT_REFUSE = "refuse"
STATUTS = (
    STATUT_NOUVELLE,
    STATUT_A_ANALYSER,
    STATUT_A_REVOIR,
    STATUT_PROPOSE,
    STATUT_VALIDE,
    STATUT_REFUSE,
)
# Qualification de la demande, avant toute proposition. Distincte de STATUTS.
QUALIF_INCOMPLET = "incomplet"
QUALIF_EN_COURS = "en_cours"
QUALIF_PRET_RELECTURE = "pret_relecture"
QUALIF_PRET_PROPOSITION = "pret_proposition"
QUALIFICATIONS = (
    QUALIF_INCOMPLET,
    QUALIF_EN_COURS,
    QUALIF_PRET_RELECTURE,
    QUALIF_PRET_PROPOSITION,
)
QUALIFICATION_LABELS = {
    QUALIF_INCOMPLET: "Incomplète",
    QUALIF_EN_COURS: "En cours",
    QUALIF_PRET_RELECTURE: "Prête pour relecture",
    QUALIF_PRET_PROPOSITION: "Prête pour proposition",
}
STATUT_LABELS = {
    STATUT_NOUVELLE: "Nouvelle",
    STATUT_A_ANALYSER: "À analyser",
    STATUT_A_REVOIR: "À revoir",
    STATUT_PROPOSE: "Proposée",
    STATUT_VALIDE: "Validée",
    STATUT_REFUSE: "Refusée",
}

# Comptes voyageurs.
ITERATIONS = 260_000
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
USER_ID_PREFIX = "usr_"

# Sessions du portail (en mémoire serveur).
SESSION_COOKIE = "detour_portail"
SESSION_MAX = 60_000

# Proposition statuses.
STATUT_BROUILLON = "brouillon"
STATUT_ENVOYEE = "envoyee"
STATUT_VALIDEE = "validee"
STATUT_REFUSEE = "refusee"
PROP_STATUTS = (STATUT_BROUILLON, STATUT_ENVOYEE, STATUT_VALIDEE, STATUT_REFUSEE)
PROP_STATUT_LABELS = {
    STATUT_BROUILLON: "Brouillon",
    STATUT_ENVOYEE: "Envoyée",
    STATUT_VALIDEE: "Validée",
    STATUT_REFUSEE: "Refusée",
}

# Advisor decision on a changed proposal line (does not send or book).
DECISION_KEEP = "keep"
DECISION_REPLACE = "replace"
DECISION_DROP = "drop"
DECISIONS_PRESTATION = (DECISION_KEEP, DECISION_REPLACE, DECISION_DROP)
DECISION_LABELS = {
    DECISION_KEEP: "Garder",
    DECISION_REPLACE: "Remplacer",
    DECISION_DROP: "Retirer",
}

# Google OAuth (Authorization Code + PKCE).
GOOGLE_OAUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"