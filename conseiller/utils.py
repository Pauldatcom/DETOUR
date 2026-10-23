"""Définitions globales de l'application conseiller DÉTOUR.

Ce module centralise les constantes partagées (contrat métier, limites,
identifiants d'outils) pour qu'elles restent visibles dans le dépôt.
Les valeurs secrètes ou déployables (clés, URL effectives, modèle choisi)
restent dans l'environnement ou `.env`, jamais ici.
"""

import re
import unicodedata

# Fournisseur de prestations (surchargeable par TRAVEL_API_URL).
DEFAULT_URL = "http://127.0.0.1:8765"
SOURCE_LABEL = "Serveur fictif DÉTOUR"

# Agent conversationnel (surchargeable par OPENROUTER_MODEL).
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "nvidia/nemotron-3.5-super-vl:free"
MAX_MESSAGES = 40
MAX_TOOL_ITERATIONS = 3
TOOL_NAME = "chercher_voyages"

# Provider LLM (openrouter | anthropic). Sélectionne l'implémentation de llm.py.
LLM_PROVIDER = "openrouter"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-sonnet-4-20250514"

# Contrat métier partagé avec le serveur fictif.
TYPES_VOYAGE = ("trek-randonnee", "lune-de-miel", "voyage-familial", "autres")
NIVEAUX_AVENTURE = ("calme", "modere", "intense")
ACTIVITES_POSSIBLES = ("créatif", "jeu", "cuisine", "intérieur", "extérieur", "train", "sans voiture")

# Conditional questions (#22). App-side only: never sent to the fictional server.
TYPES_ACTIVITE_PHYSIQUE = ("trek-randonnee",)
TYPES_AVEC_GUIDE = ("trek-randonnee",)

# Statuts d'une demande.
STATUT_NOUVELLE = "nouvelle"
STATUT_A_ANALYSER = "a_analyser"
STATUT_A_REVOIR = "a_revoir"  # To review — price or availability changed after v1.
# #52: Answered — set only by recording the advisor's response (never by a bare
# status change), so an answered request always carries who answered and when.
STATUT_REPONDUE = "repondue"
STATUT_PROPOSE = "propose"
STATUT_VALIDE = "valide"
STATUT_REFUSE = "refuse"
STATUTS = (
    STATUT_NOUVELLE,
    STATUT_A_ANALYSER,
    STATUT_A_REVOIR,
    STATUT_REPONDUE,
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
    STATUT_REPONDUE: "Répondue",
    STATUT_PROPOSE: "Proposée",
    STATUT_VALIDE: "Validée",
    STATUT_REFUSE: "Refusée",
}

# Transitions de statut autorisées pour une demande. Un statut absent de la
# liste est terminal : aucune décision ne peut le faire bouger.
TRANSITIONS_DEMANDE = {
    # #49: submitted (nouvelle) can be taken in charge, refused, or flagged
    # to review after a re-read — without claiming an advisor already analysed it.
    # #52: it can also be answered (Answered) by the advisor.
    STATUT_NOUVELLE: frozenset({STATUT_A_ANALYSER, STATUT_A_REVOIR, STATUT_REPONDUE, STATUT_REFUSE}),
    STATUT_A_ANALYSER: frozenset({STATUT_A_REVOIR, STATUT_REPONDUE, STATUT_PROPOSE, STATUT_VALIDE, STATUT_REFUSE}),
    STATUT_A_REVOIR: frozenset({STATUT_A_ANALYSER, STATUT_REPONDUE, STATUT_PROPOSE, STATUT_VALIDE, STATUT_REFUSE}),
    # #52: once answered, the request goes on with the usual workflow.
    STATUT_REPONDUE: frozenset({STATUT_A_ANALYSER, STATUT_A_REVOIR, STATUT_PROPOSE, STATUT_VALIDE, STATUT_REFUSE}),
    STATUT_PROPOSE: frozenset({STATUT_VALIDE, STATUT_REFUSE, STATUT_A_ANALYSER, STATUT_A_REVOIR}),
    STATUT_VALIDE: frozenset(),
    STATUT_REFUSE: frozenset(),
}
# #52: maximum length of the advisor's written response to a request.
REPONSE_MAX_CARACTERES = 5000

# Comptes voyageurs.
ITERATIONS = 260_000
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
USER_ID_PREFIX = "usr_"

# Sessions du portail (en mémoire serveur).
SESSION_COOKIE = "detour_portail"
SESSION_MAX = 60_000

# Proposition statuses.
# A proposal waits for the advisor (pending), is accepted, sent back for a
# correction, or rejected. "envoyee" means the advisor approved it and it
# goes to the traveler; "validee" means the traveler confirmed it.
STATUT_BROUILLON = "brouillon"
STATUT_ENVOYEE = "envoyee"
STATUT_VALIDEE = "validee"
STATUT_REFUSEE = "refusee"
STATUT_CORRECTION_DEMANDEE = "correction_requested"
PROP_STATUTS = (
    STATUT_BROUILLON,
    STATUT_ENVOYEE,
    STATUT_VALIDEE,
    STATUT_REFUSEE,
    STATUT_CORRECTION_DEMANDEE,
)
PROP_STATUT_LABELS = {
    STATUT_BROUILLON: "Brouillon",
    STATUT_ENVOYEE: "Envoyée",
    STATUT_VALIDEE: "Validée",
    STATUT_REFUSEE: "Refusée",
    STATUT_CORRECTION_DEMANDEE: "Correction demandée",
}

# Transitions de statut autorisées pour une proposition. Validee et refusee
# sont terminales : une proposition envoyée ne revient pas en brouillon.
# Une correction demandée peut être reprise puis réexaminée.
TRANSITIONS_PROPOSITION = {
    STATUT_BROUILLON: frozenset({
        STATUT_ENVOYEE, STATUT_REFUSEE, STATUT_CORRECTION_DEMANDEE}),
    STATUT_CORRECTION_DEMANDEE: frozenset({
        STATUT_BROUILLON, STATUT_ENVOYEE, STATUT_REFUSEE}),
    STATUT_ENVOYEE: frozenset({STATUT_VALIDEE, STATUT_REFUSEE}),
    STATUT_VALIDEE: frozenset(),
    STATUT_REFUSEE: frozenset(),
}

# Advisor decision on a proposal: the three actions the interface offers.
DECISION_ACCEPTER = "accepter"
DECISION_CORRECTION = "demander_correction"
DECISION_REFUSER = "refuser"
DECISION_ACTIONS = (DECISION_ACCEPTER, DECISION_CORRECTION, DECISION_REFUSER)
# Status reached by each decision.
STATUT_PAR_DECISION = {
    DECISION_ACCEPTER: STATUT_ENVOYEE,
    DECISION_CORRECTION: STATUT_CORRECTION_DEMANDEE,
    DECISION_REFUSER: STATUT_REFUSEE,
}
# Decisions that must carry a reason. Accepting may go without one.
DECISIONS_AVEC_MOTIF = (DECISION_CORRECTION, DECISION_REFUSER)

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

# The agent is never an authorized actor for a human decision.
ACTEUR_AGENT = "agent"

# Google OAuth (Authorization Code + PKCE).
GOOGLE_OAUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

# Advisor first name (#112): it signs proposals and decisions for travelers.
PRENOM_CONSEILLER_DEFAUT = "Conseiller DÉTOUR"
PRENOM_MAX = 40
_PRENOM_RE = re.compile(r"[^\W\d_]+(?:[ '’-][^\W\d_]+)*")


def valider_prenom_conseiller(valeur):
    """Return a clean first name, the default when absent, or raise ValueError.

    NFC normalization first, so an accent typed as a separate combining
    character ("e" + U+0301) is accepted like "é".
    """
    if valeur is None:
        return PRENOM_CONSEILLER_DEFAUT
    if not isinstance(valeur, str):
        raise ValueError("Le prénom doit être un texte.")
    prenom = " ".join(unicodedata.normalize("NFC", valeur).split())
    if not prenom:
        return PRENOM_CONSEILLER_DEFAUT
    if len(prenom) > PRENOM_MAX or not _PRENOM_RE.fullmatch(prenom):
        raise ValueError(
            "Le prénom ne doit contenir que des lettres, espaces, tirets ou apostrophes.")
    return prenom
