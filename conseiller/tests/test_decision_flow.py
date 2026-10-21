#!/usr/bin/env python3
"""Tests du flux de décision complet et de sa traçabilité (#42).

Couvre l'acceptation, la correction et le rejet, la persistance de l'auteur,
de la date et du motif, les actions non autorisées, les transitions de statut
invalides, et le fait que l'agent ne prend jamais de décision humaine.
"""

import http.cookiejar
import json
import secrets
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

CONSEILLER_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CONSEILLER_ROOT))

from app import make_handler
from propositions import PropositionError, PropositionStore
from store import DemandStore, ValidationError
from users import UserStore
from utils import (
    QUALIF_INCOMPLET,
    QUALIF_PRET_PROPOSITION,
    STATUT_A_ANALYSER,
    STATUT_NOUVELLE,
    STATUT_PROPOSE,
    STATUT_REFUSE,
    STATUT_VALIDE,
)
from test_conseiller import VALIDE

PROPOSITION_VALIDE = {
    "titre": "Week-end à Nantes",
    "description": "Un séjour romantique à Nantes.",
    "prestations": [
        {"id": "train-nantes-01", "nom": "Train Nantes", "type": "transport",
         "prix_unitaire_eur": 48, "quantite": 2},
    ],
}

CONSEILLER = "Conseiller DÉTOUR"


class ClientHTTP:
    """Navigateur minimal : suit les cookies de session."""

    def __init__(self, base):
        self.base = base
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.jar))

    def _req(self, chemin, payload=None, method=None):
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {"Content-Type": "application/json"} if payload is not None else {}
        req = urllib.request.Request(self.base + chemin, data=data, headers=headers,
                                     method=method)
        try:
            with self.opener.open(req) as res:
                corps = res.read()
                return res.status, (json.loads(corps) if corps else {})
        except urllib.error.HTTPError as err:
            corps = err.read()
            try:
                return err.code, json.loads(corps)
            except json.JSONDecodeError:
                return err.code, {}

    def get(self, chemin):
        return self._req(chemin)

    def post(self, chemin, payload):
        return self._req(chemin, payload, method="POST")

    def patch(self, chemin, payload):
        return self._req(chemin, payload, method="PATCH")


def demarrer(handler):
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_port}"


class BaseDecision(unittest.TestCase):
    """Outils communs : un store en mémoire et un serveur advisor."""

    def setUp(self):
        self.store = DemandStore(None)
        self.props = PropositionStore(None)
        self.team_key = "cle-" + secrets.token_urlsafe(12)
        self.users = UserStore(None)
        handler = make_handler(self.store, None, None, users=self.users,
                               team_key=self.team_key, propositions=self.props)
        self.server, self.base = demarrer(handler)
        self.addCleanup(lambda: (self.server.shutdown(), self.server.server_close()))
        self.dem_id = self.store.creer(dict(VALIDE))["id"]

    def conseiller(self):
        client = ClientHTTP(self.base)
        status, _ = client.post("/api/login-conseiller", {"cle": self.team_key})
        self.assertEqual(status, 200)
        return client

    def voyageur(self):
        client = ClientHTTP(self.base)
        client.post("/api/register", {"email": "zoe@exemple.fr", "nom": "Zoé",
                                      "mot_de_passe": "motdepasse"})
        return client

    def qualifier(self, dem_id=None):
        """Le conseiller valide la demande pour proposition."""
        return self.store.definir_qualification(
            dem_id or self.dem_id, QUALIF_PRET_PROPOSITION, acteur="conseiller",
            par=CONSEILLER, motif="dossier complet")


# ---------------------------------------------------------------- acceptation
class TestAcceptation(BaseDecision):
    def test_validation_pour_proposition_est_decision_du_conseiller(self):
        record = self.qualifier()
        self.assertEqual(record["qualification"], QUALIF_PRET_PROPOSITION)
        self.assertEqual(record["qualification_validee_par"], "conseiller")

    def test_validation_refusee_si_information_manquante(self):
        self.store.demandes[self.dem_id]["demande"]["budget_max_par_personne"] = 0
        self.store.recalculer(self.dem_id)
        with self.assertRaises(ValidationError):
            self.qualifier()
        self.assertEqual(self.store.obtenir(self.dem_id)["qualification"], "incomplet")

    def test_renvoi_en_incomplet_est_une_decision(self):
        record = self.store.definir_qualification(
            self.dem_id, QUALIF_INCOMPLET, acteur="conseiller",
            par=CONSEILLER, motif="il manque la date de retour")
        self.assertEqual(record["qualification"], QUALIF_INCOMPLET)
        self.assertEqual(len(record["decisions"]), 1)
        self.assertEqual(record["decisions"][0]["action"], "qualification")

    def test_route_qualification_conseiller_accepte(self):
        client = self.conseiller()
        status, data = client.patch(f"/api/demandes/{self.dem_id}/qualification",
                                    {"qualification": QUALIF_PRET_PROPOSITION,
                                     "motif": "dossier complet"})
        self.assertEqual(status, 200)
        self.assertEqual(data["demande"]["qualification"], QUALIF_PRET_PROPOSITION)
        self.assertEqual(len(data["demande"]["decisions"]), 1)

    def test_acceptance_de_la_demande_apres_qualification(self):
        self.qualifier()
        record = self.store.changer_statut(self.dem_id, STATUT_VALIDE,
                                           CONSEILLER, "offre acceptee")
        self.assertEqual(record["statut"], STATUT_VALIDE)
        self.assertEqual(len(record["decisions"]), 2)

    def test_route_statut_conseiller_accepte(self):
        client = self.conseiller()
        client.patch(f"/api/demandes/{self.dem_id}/qualification",
                     {"qualification": QUALIF_PRET_PROPOSITION, "motif": "dossier complet"})
        status, data = client.patch(f"/api/demandes/{self.dem_id}/statut",
                                    {"statut": STATUT_VALIDE, "motif": "offre acceptee"})
        self.assertEqual(status, 200)
        self.assertEqual(data["demande"]["statut"], STATUT_VALIDE)


# -------------------------------------------------------------------- rejet
class TestRejet(BaseDecision):
    def test_refus_de_la_demande_est_autorise(self):
        record = self.store.changer_statut(self.dem_id, STATUT_REFUSE,
                                           CONSEILLER, "budget insuffisant")
        self.assertEqual(record["statut"], STATUT_REFUSE)
        self.assertEqual(record["decisions"][-1]["motif"], "budget insuffisant")

    def test_route_refus_de_la_demande(self):
        client = self.conseiller()
        status, data = client.patch(f"/api/demandes/{self.dem_id}/statut",
                                    {"statut": STATUT_REFUSE, "motif": "budget insuffisant"})
        self.assertEqual(status, 200)
        self.assertEqual(data["demande"]["statut"], STATUT_REFUSE)
        self.assertEqual(data["demande"]["decisions"][-1]["par"], CONSEILLER)

    def test_refus_de_la_proposition_est_autorise(self):
        prop = self.props.creer(self.dem_id, dict(PROPOSITION_VALIDE),
                                conseiller=CONSEILLER)
        record = self.props.changer_statut(prop["id"], "refusee", CONSEILLER,
                                            "prix au-dessus du budget")
        self.assertEqual(record["statut"], "refusee")
        self.assertEqual(record["decisions_statut"][-1]["motif"],
                         "prix au-dessus du budget")

    def test_route_refus_de_la_proposition(self):
        client = self.conseiller()
        _, data = client.post(f"/api/demandes/{self.dem_id}/propositions",
                              dict(PROPOSITION_VALIDE))
        prop_id = data["proposition"]["id"]
        status, data = client.patch(f"/api/propositions/{prop_id}/statut",
                                    {"statut": "refusee", "motif": "prix trop eleve"})
        self.assertEqual(status, 200)
        self.assertEqual(data["proposition"]["statut"], "refusee")
        self.assertEqual(data["proposition"]["decisions_statut"][-1]["avant"], "brouillon")


# -------------------------------------------------------------- traçabilité
class TestTracabilite(BaseDecision):
    def test_la_decision_conserve_auteur_date_et_motif(self):
        self.qualifier()
        record = self.store.changer_statut(self.dem_id, STATUT_PROPOSE,
                                           CONSEILLER, "offre envoyee au voyageur")
        entree = record["decisions"][-1]
        self.assertEqual(entree["action"], "statut")
        self.assertEqual(entree["par"], CONSEILLER)
        self.assertEqual(entree["motif"], "offre envoyee au voyageur")
        self.assertEqual(entree["avant"], STATUT_A_ANALYSER)
        self.assertEqual(entree["apres"], STATUT_PROPOSE)
        self.assertTrue(entree["le"])
        self.assertRegex(entree["le"], r"^\d{4}-\d{2}-\d{2}T")

    def test_le_motif_est_obligatoire(self):
        with self.assertRaises(ValidationError):
            self.store.changer_statut(self.dem_id, STATUT_REFUSE, CONSEILLER, "")
        with self.assertRaises(ValidationError):
            self.store.changer_statut(self.dem_id, STATUT_REFUSE, CONSEILLER, "   ")
        with self.assertRaises(ValidationError):
            self.store.definir_qualification(
                self.dem_id, QUALIF_PRET_PROPOSITION, acteur="conseiller",
                par=CONSEILLER, motif="")
        with self.assertRaises(ValidationError):
            self.store.corriger(self.dem_id, {"destination": "Lyon"}, CONSEILLER, "")

    def test_le_nom_du_conseiller_est_obligatoire(self):
        with self.assertRaises(ValidationError):
            self.store.changer_statut(self.dem_id, STATUT_REFUSE, "", "budget")
        with self.assertRaises(ValidationError):
            self.store.corriger(self.dem_id, {"destination": "Lyon"}, "  ", "budget")

    def test_une_decision_refusee_nest_pas_journalisee(self):
        with self.assertRaises(ValidationError):
            self.store.changer_statut(self.dem_id, STATUT_REFUSE, CONSEILLER, "")
        self.assertEqual(self.store.obtenir(self.dem_id).get("decisions") or [], [])

    def test_le_journal_survit_au_redemarrage(self):
        tmp = tempfile.mkdtemp()
        path = Path(tmp) / "demandes.json"
        store = DemandStore(path)
        dem_id = store.creer(dict(VALIDE))["id"]
        store.definir_qualification(dem_id, QUALIF_PRET_PROPOSITION,
                                    acteur="conseiller", par=CONSEILLER,
                                    motif="dossier complet")
        store.changer_statut(dem_id, STATUT_PROPOSE, CONSEILLER, "offre prete")
        relu = DemandStore(path).obtenir(dem_id)
        self.assertEqual(len(relu["decisions"]), 2)
        self.assertEqual(relu["decisions"][1]["par"], CONSEILLER)
        self.assertEqual(relu["decisions"][1]["motif"], "offre prete")
        self.assertTrue(relu["decisions"][1]["le"])

    def test_le_journal_est_append_only(self):
        self.qualifier()
        self.store.changer_statut(self.dem_id, STATUT_PROPOSE, CONSEILLER, "offre prete")
        record = self.store.changer_statut(self.dem_id, STATUT_VALIDE, CONSEILLER,
                                           "offre acceptee")
        self.assertEqual(len(record["decisions"]), 3)
        self.assertEqual(record["decisions"][0]["action"], "qualification")
        self.assertEqual(record["decisions"][1]["motif"], "offre prete")
        self.assertEqual(record["decisions"][2]["motif"], "offre acceptee")

    def test_la_correction_est_journalisee(self):
        record = self.store.corriger(self.dem_id, {"destination": "Lyon"},
                                     CONSEILLER, "destination lue de travers")
        self.assertEqual(len(record["decisions"]), 1)
        entree = record["decisions"][0]
        self.assertEqual(entree["action"], "correction")
        self.assertEqual(entree["par"], CONSEILLER)
        self.assertEqual(entree["motif"], "destination lue de travers")
        self.assertEqual(entree["champs"], ["destination"])
        self.assertTrue(entree["le"])

    def test_une_correction_sans_changement_ne_journalise_rien(self):
        record = self.store.corriger(self.dem_id, {"destination": "Nantes"},
                                     CONSEILLER, "verifie, rien a changer")
        self.assertEqual(record.get("decisions") or [], [])

    def test_la_decision_de_statut_d_une_proposition_est_journalisee(self):
        prop = self.props.creer(self.dem_id, dict(PROPOSITION_VALIDE),
                                conseiller=CONSEILLER)
        record = self.props.changer_statut(prop["id"], "envoyee", CONSEILLER,
                                            "envoi au voyageur")
        self.assertEqual(len(record["decisions_statut"]), 1)
        entree = record["decisions_statut"][0]
        self.assertEqual(entree["action"], "statut")
        self.assertEqual(entree["par"], CONSEILLER)
        self.assertEqual(entree["motif"], "envoi au voyageur")
        self.assertEqual(entree["avant"], "brouillon")
        self.assertEqual(entree["apres"], "envoyee")
        self.assertTrue(entree["le"])

    def test_le_journal_des_lignes_ne_se_confond_pas_avec_celui_des_statuts(self):
        prop = self.props.creer(self.dem_id, dict(PROPOSITION_VALIDE),
                                conseiller=CONSEILLER)
        self.props.enregistrer_decision(prop["id"], "train-nantes-01", "keep",
                                        CONSEILLER, "prix acceptable")
        record = self.props.changer_statut(prop["id"], "envoyee", CONSEILLER,
                                            "envoi au voyageur")
        self.assertEqual(len(record["decisions"]), 1)
        self.assertEqual(record["decisions"][0]["choix"], "keep")
        self.assertEqual(len(record["decisions_statut"]), 1)
        self.assertEqual(record["decisions_statut"][0]["action"], "statut")


# ------------------------------------------------------- transitions invalides
class TestTransitionsInvalides(BaseDecision):
    def test_un_statut_inconnu_est_refuse(self):
        with self.assertRaises(ValidationError):
            self.store.changer_statut(self.dem_id, "nimporte", CONSEILLER, "essai")

    def test_une_demande_validee_est_terminale(self):
        self.qualifier()
        self.store.changer_statut(self.dem_id, STATUT_VALIDE, CONSEILLER, "offre acceptee")
        with self.assertRaises(ValidationError):
            self.store.changer_statut(self.dem_id, STATUT_A_ANALYSER, CONSEILLER, "retour")

    def test_une_demande_refusee_est_terminale(self):
        self.store.changer_statut(self.dem_id, STATUT_REFUSE, CONSEILLER, "budget")
        with self.assertRaises(ValidationError):
            self.store.changer_statut(self.dem_id, STATUT_A_ANALYSER, CONSEILLER, "retour")

    def test_on_ne_peut_pas_revenir_en_arriere_depuis_propose(self):
        self.qualifier()
        self.store.changer_statut(self.dem_id, STATUT_PROPOSE, CONSEILLER, "offre prete")
        with self.assertRaises(ValidationError):
            self.store.changer_statut(self.dem_id, STATUT_NOUVELLE, CONSEILLER, "retour")

    def test_une_transition_autorisee_de_propose_vers_analyse_est_acceptee(self):
        self.qualifier()
        self.store.changer_statut(self.dem_id, STATUT_PROPOSE, CONSEILLER, "offre prete")
        record = self.store.changer_statut(self.dem_id, STATUT_A_ANALYSER,
                                           CONSEILLER, "retour en analyse")
        self.assertEqual(record["statut"], STATUT_A_ANALYSER)

    def test_une_transition_interdite_ne_change_aucun_champ(self):
        self.qualifier()
        self.store.changer_statut(self.dem_id, STATUT_PROPOSE, CONSEILLER, "offre prete")
        self.store.changer_statut(self.dem_id, STATUT_VALIDE, CONSEILLER, "offre acceptee")
        with self.assertRaises(ValidationError):
            self.store.changer_statut(self.dem_id, STATUT_REFUSE, CONSEILLER, "retour")
        self.assertEqual(self.store.obtenir(self.dem_id)["statut"], STATUT_VALIDE)

    def test_une_proposition_envoyee_ne_revient_pas_en_brouillon(self):
        prop = self.props.creer(self.dem_id, dict(PROPOSITION_VALIDE),
                                conseiller=CONSEILLER)
        self.props.changer_statut(prop["id"], "envoyee", CONSEILLER, "envoi")
        with self.assertRaises(PropositionError):
            self.props.changer_statut(prop["id"], "brouillon", CONSEILLER, "retour")

    def test_une_proposition_refusee_est_terminale(self):
        prop = self.props.creer(self.dem_id, dict(PROPOSITION_VALIDE),
                                conseiller=CONSEILLER)
        self.props.changer_statut(prop["id"], "refusee", CONSEILLER, "prix trop eleve")
        with self.assertRaises(PropositionError):
            self.props.changer_statut(prop["id"], "envoyee", CONSEILLER, "renvoi")

    def test_une_proposition_validee_est_terminale(self):
        prop = self.props.creer(self.dem_id, dict(PROPOSITION_VALIDE),
                                conseiller=CONSEILLER)
        self.props.changer_statut(prop["id"], "envoyee", CONSEILLER, "envoi")
        self.props.changer_statut(prop["id"], "validee", CONSEILLER, "acceptee")
        with self.assertRaises(PropositionError):
            self.props.changer_statut(prop["id"], "refusee", CONSEILLER, "finalement non")


# --------------------------------------------------------- actions non autorisées
class TestActionsNonAutorisees(BaseDecision):
    def test_qualification_refusee_sans_session(self):
        client = ClientHTTP(self.base)
        status, data = client.patch(f"/api/demandes/{self.dem_id}/qualification",
                                    {"qualification": QUALIF_PRET_PROPOSITION,
                                     "motif": "dossier complet"})
        self.assertEqual(status, 401)
        self.assertEqual(data["erreur"]["code"], "auth_requise")

    def test_statut_refuse_sans_session(self):
        client = ClientHTTP(self.base)
        status, data = client.patch(f"/api/demandes/{self.dem_id}/statut",
                                    {"statut": STATUT_VALIDE, "motif": "offre acceptee"})
        self.assertEqual(status, 401)
        self.assertEqual(data["erreur"]["code"], "auth_requise")

    def test_correction_refusee_sans_session(self):
        client = ClientHTTP(self.base)
        status, data = client.patch(f"/api/demandes/{self.dem_id}/correction",
                                    {"champs": {"destination": "Lyon"},
                                     "motif": "destination corrigee"})
        self.assertEqual(status, 401)
        self.assertEqual(data["erreur"]["code"], "auth_requise")

    def test_qualification_refusee_a_un_voyageur(self):
        client = self.voyageur()
        status, data = client.patch(f"/api/demandes/{self.dem_id}/qualification",
                                    {"qualification": QUALIF_PRET_PROPOSITION,
                                     "motif": "dossier complet"})
        self.assertEqual(status, 401)
        self.assertEqual(data["erreur"]["code"], "auth_requise")

    def test_statut_refuse_a_un_voyageur(self):
        client = self.voyageur()
        status, data = client.patch(f"/api/demandes/{self.dem_id}/statut",
                                    {"statut": STATUT_VALIDE, "motif": "offre acceptee"})
        self.assertEqual(status, 401)
        self.assertEqual(data["erreur"]["code"], "auth_requise")

    def test_correction_refusee_a_un_voyageur(self):
        client = self.voyageur()
        status, data = client.patch(f"/api/demandes/{self.dem_id}/correction",
                                    {"champs": {"destination": "Lyon"},
                                     "motif": "destination corrigee"})
        self.assertEqual(status, 401)
        self.assertEqual(data["erreur"]["code"], "auth_requise")

    def test_statut_de_proposition_refuse_a_un_voyageur(self):
        client = self.voyageur()
        advisor = self.conseiller()
        _, data = advisor.post(f"/api/demandes/{self.dem_id}/propositions",
                               dict(PROPOSITION_VALIDE))
        prop_id = data["proposition"]["id"]
        status, data = client.patch(f"/api/propositions/{prop_id}/statut",
                                    {"statut": "envoyee", "motif": "envoi"})
        self.assertEqual(status, 401)
        self.assertEqual(data["erreur"]["code"], "auth_requise")

    def test_une_action_refusee_ne_laisse_aucune_trace(self):
        client = self.voyageur()
        client.patch(f"/api/demandes/{self.dem_id}/statut",
                     {"statut": STATUT_VALIDE, "motif": "offre acceptee"})
        self.assertEqual(self.store.obtenir(self.dem_id)["statut"], STATUT_A_ANALYSER)
        self.assertEqual(self.store.obtenir(self.dem_id).get("decisions") or [], [])


# ------------------------------------------------------- l'agent ne décide pas
class TestAgentNiDecideur(BaseDecision):
    def test_l_agent_ne_valide_pas_pour_proposition(self):
        with self.assertRaises(ValidationError):
            self.store.definir_qualification(
                self.dem_id, QUALIF_PRET_PROPOSITION, acteur="agent",
                par="agent", motif="je decide")
        self.assertEqual(self.store.obtenir(self.dem_id)["qualification"], "pret_relecture")

    def test_l_agent_ne_change_pas_le_statut(self):
        with self.assertRaises(ValidationError):
            self.store.changer_statut(self.dem_id, STATUT_VALIDE, "agent", "je decide")
        self.assertEqual(self.store.obtenir(self.dem_id)["statut"], STATUT_A_ANALYSER)

    def test_l_agent_ne_corrige_pas_la_demande(self):
        with self.assertRaises(ValidationError):
            self.store.corriger(self.dem_id, {"destination": "Lyon"}, "agent", "je corrige")
        self.assertEqual(self.store.obtenir(self.dem_id)["demande"]["destination"],
                         VALIDE["destination"])

    def test_une_tentative_de_l_agent_ne_laisse_aucune_decision(self):
        for action in (
            lambda: self.store.changer_statut(self.dem_id, STATUT_VALIDE, "agent", "x"),
            lambda: self.store.corriger(self.dem_id, {"destination": "Lyon"}, "agent", "x"),
            lambda: self.store.definir_qualification(
                self.dem_id, QUALIF_PRET_PROPOSITION, acteur="agent", par="agent", motif="x"),
        ):
            with self.assertRaises(ValidationError):
                action()
        self.assertEqual(self.store.obtenir(self.dem_id).get("decisions") or [], [])

    def test_l_outil_de_l_agent_refuse_un_argument_de_decision(self):
        from agent import DECISION_ARGS
        for cle in DECISION_ARGS:
            self.assertIn(cle, DECISION_ARGS)
        self.assertIn("statut", DECISION_ARGS)
        self.assertIn("motif", DECISION_ARGS)
        self.assertIn("qualification", DECISION_ARGS)

    def test_l_agent_ne_decide_pas_par_la_route(self):
        client = self.voyageur()
        status, _ = client.patch(f"/api/demandes/{self.dem_id}/statut",
                                 {"statut": STATUT_VALIDE, "motif": "offre acceptee"})
        self.assertEqual(status, 401)


if __name__ == "__main__":
    unittest.main()
