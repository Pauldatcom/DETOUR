#!/usr/bin/env python3
"""Tests des décisions du conseiller sur une proposition (#28, #32).

Couvre les trois actions (accepter, demander une correction, refuser), la
représentation partagée de la décision (auteur, date, motif, instructions,
version visée) et le refus d'une action que l'état courant n'autorise pas.
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
from store import DemandStore
from users import UserStore
from utils import (
    DECISION_ACCEPTER,
    DECISION_CORRECTION,
    DECISION_REFUSER,
    STATUT_BROUILLON,
    STATUT_CORRECTION_DEMANDEE,
    STATUT_ENVOYEE,
    STATUT_REFUSEE,
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


class BaseDecisionProposition(unittest.TestCase):
    """Un store, un serveur et une proposition en brouillon."""

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
        self.prop = self.props.creer(self.dem_id, dict(PROPOSITION_VALIDE),
                                     conseiller=CONSEILLER)

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


# ------------------------------------------------------- représentation (#28)
class TestRepresentationDecision(unittest.TestCase):
    """La décision partagée : action, auteur, date, motif, version visée."""

    def setUp(self):
        self.props = PropositionStore(None)
        self.prop = self.props.creer("dem_abc", dict(PROPOSITION_VALIDE),
                                     conseiller=CONSEILLER)

    def test_la_decision_conserve_action_auteur_date_et_motif(self):
        record = self.props.decider(self.prop["id"], DECISION_ACCEPTER, CONSEILLER,
                                    "prix conforme au budget")
        self.assertEqual(record["statut"], STATUT_ENVOYEE)
        self.assertEqual(len(record["decisions_statut"]), 1)
        entree = record["decisions_statut"][0]
        self.assertEqual(entree["action"], DECISION_ACCEPTER)
        self.assertEqual(entree["par"], CONSEILLER)
        self.assertEqual(entree["motif"], "prix conforme au budget")
        self.assertEqual(entree["avant"], STATUT_BROUILLON)
        self.assertEqual(entree["apres"], STATUT_ENVOYEE)
        self.assertTrue(entree["le"])
        self.assertRegex(entree["le"], r"^\d{4}-\d{2}-\d{2}T")

    def test_la_decision_est_liee_a_la_proposition_et_a_sa_version(self):
        record = self.props.decider(self.prop["id"], DECISION_ACCEPTER, CONSEILLER,
                                    "ok")
        entree = record["decisions_statut"][0]
        self.assertEqual(entree["proposition_id"], self.prop["id"])
        self.assertEqual(entree["version"], 1)

    def test_la_version_visee_est_celle_de_la_proposition_decidee(self):
        v2 = self.props.creer_v2_si_complet(self.prop["id"], None,
                                             conseiller=CONSEILLER)
        self.assertIsNone(v2)
        prop2 = self.props.creer("dem_abc", dict(PROPOSITION_VALIDE),
                                 conseiller=CONSEILLER, version=2)
        record = self.props.decider(prop2["id"], DECISION_ACCEPTER, CONSEILLER, "ok")
        self.assertEqual(record["decisions_statut"][0]["version"], 2)

    def test_instructions_kept_for_correction_only(self):
        record = self.props.decider(self.prop["id"], DECISION_CORRECTION, CONSEILLER,
                                    "prix à revoir", "proposer un train moins cher")
        entree = record["decisions_statut"][0]
        self.assertEqual(entree["instructions"], "proposer un train moins cher")
        record = self.props.decider(self.prop["id"], DECISION_ACCEPTER, CONSEILLER, "ok")
        self.assertIsNone(record["decisions_statut"][-1]["instructions"])

    def test_le_journal_des_decisions_est_append_only(self):
        self.props.decider(self.prop["id"], DECISION_CORRECTION, CONSEILLER,
                           "prix à revoir", "un train moins cher")
        record = self.props.decider(self.prop["id"], DECISION_ACCEPTER, CONSEILLER,
                                    "corrige")
        self.assertEqual(len(record["decisions_statut"]), 2)
        self.assertEqual(record["decisions_statut"][0]["action"], DECISION_CORRECTION)
        self.assertEqual(record["decisions_statut"][1]["action"], DECISION_ACCEPTER)

    def test_le_journal_survit_au_redemarrage(self):
        tmp = tempfile.mkdtemp()
        path = Path(tmp) / "propositions.json"
        props = PropositionStore(path)
        prop = props.creer("dem_abc", dict(PROPOSITION_VALIDE), conseiller=CONSEILLER)
        props.decider(prop["id"], DECISION_REFUSER, CONSEILLER, "budget insuffisant")
        relu = PropositionStore(path).obtenir(prop["id"])
        self.assertEqual(len(relu["decisions_statut"]), 1)
        self.assertEqual(relu["decisions_statut"][0]["motif"], "budget insuffisant")
        self.assertTrue(relu["decisions_statut"][0]["le"])

    def test_le_journal_des_lignes_reste_separe(self):
        self.props.decider(self.prop["id"], DECISION_ACCEPTER, CONSEILLER, "ok")
        record = self.props.enregistrer_decision(
            self.prop["id"], "train-nantes-01", "keep", CONSEILLER, "prix acceptable")
        self.assertEqual(len(record["decisions"]), 1)
        self.assertEqual(record["decisions"][0]["choix"], "keep")
        self.assertEqual(len(record["decisions_statut"]), 1)


# ------------------------------------------------------------- actions (#32)
class TestActionsDecision(unittest.TestCase):
    def setUp(self):
        self.props = PropositionStore(None)
        self.prop = self.props.creer("dem_abc", dict(PROPOSITION_VALIDE),
                                     conseiller=CONSEILLER)

    def test_accepter_envoie_la_proposition(self):
        record = self.props.decider(self.prop["id"], DECISION_ACCEPTER, CONSEILLER, "ok")
        self.assertEqual(record["statut"], STATUT_ENVOYEE)

    def test_demander_une_correction_ouvre_un_nouveau_statut(self):
        record = self.props.decider(self.prop["id"], DECISION_CORRECTION, CONSEILLER,
                                    "prix trop eleve", "un train moins cher")
        self.assertEqual(record["statut"], STATUT_CORRECTION_DEMANDEE)

    def test_refuser_est_definitif(self):
        record = self.props.decider(self.prop["id"], DECISION_REFUSER, CONSEILLER,
                                    "budget insuffisant")
        self.assertEqual(record["statut"], STATUT_REFUSEE)
        with self.assertRaises(PropositionError):
            self.props.decider(self.prop["id"], DECISION_ACCEPTER, CONSEILLER, "ok")

    def test_une_correction_exige_un_motif(self):
        with self.assertRaises(PropositionError):
            self.props.decider(self.prop["id"], DECISION_CORRECTION, CONSEILLER,
                               "", "instructions")
        with self.assertRaises(PropositionError):
            self.props.decider(self.prop["id"], DECISION_CORRECTION, CONSEILLER,
                               "   ", "instructions")

    def test_une_correction_exige_des_instructions(self):
        with self.assertRaises(PropositionError):
            self.props.decider(self.prop["id"], DECISION_CORRECTION, CONSEILLER,
                               "prix trop eleve", "")

    def test_un_refus_exige_un_motif(self):
        with self.assertRaises(PropositionError):
            self.props.decider(self.prop["id"], DECISION_REFUSER, CONSEILLER, "")

    def test_accepter_va_sans_motif(self):
        record = self.props.decider(self.prop["id"], DECISION_ACCEPTER, CONSEILLER)
        self.assertEqual(record["statut"], STATUT_ENVOYEE)
        self.assertEqual(record["decisions_statut"][-1]["motif"], "")

    def test_le_nom_du_conseiller_est_obligatoire(self):
        with self.assertRaises(PropositionError):
            self.props.decider(self.prop["id"], DECISION_ACCEPTER, "", "ok")

    def test_une_action_inconnue_est_refusee(self):
        with self.assertRaises(PropositionError):
            self.props.decider(self.prop["id"], "envoyer", CONSEILLER, "ok")

    def test_une_proposition_inconnue_retourne_none(self):
        self.assertIsNone(self.props.decider("prop_inconnu", DECISION_ACCEPTER,
                                             CONSEILLER, "ok"))

    def test_une_action_refusee_ne_laisse_aucune_trace(self):
        with self.assertRaises(PropositionError):
            self.props.decider(self.prop["id"], DECISION_REFUSER, CONSEILLER, "")
        self.assertEqual(self.props.obtenir(self.prop["id"])["statut"],
                         STATUT_BROUILLON)
        self.assertEqual(self.props.obtenir(self.prop["id"]).get("decisions_statut")
                         or [], [])

    def test_une_correction_demandee_peut_etre_reprise(self):
        self.props.decider(self.prop["id"], DECISION_CORRECTION, CONSEILLER,
                           "prix a revoir", "un train moins cher")
        record = self.props.decider(self.prop["id"], DECISION_ACCEPTER, CONSEILLER,
                                    "corrige")
        self.assertEqual(record["statut"], STATUT_ENVOYEE)


# --------------------------------------------------------- endpoints (#32)
class TestRoutesDecision(BaseDecisionProposition):
    def test_route_accepter(self):
        client = self.conseiller()
        status, data = client.post(
            f"/api/propositions/{self.prop['id']}/accepter",
            {"motif": "prix conforme"})
        self.assertEqual(status, 200)
        self.assertEqual(data["proposition"]["statut"], STATUT_ENVOYEE)
        self.assertEqual(data["proposition"]["decisions_statut"][-1]["action"],
                         DECISION_ACCEPTER)
        self.assertEqual(data["proposition"]["decisions_statut"][-1]["par"],
                         CONSEILLER)

    def test_route_correction(self):
        client = self.conseiller()
        status, data = client.post(
            f"/api/propositions/{self.prop['id']}/correction",
            {"motif": "prix trop eleve", "instructions": "un train moins cher"})
        self.assertEqual(status, 200)
        self.assertEqual(data["proposition"]["statut"], STATUT_CORRECTION_DEMANDEE)
        entree = data["proposition"]["decisions_statut"][-1]
        self.assertEqual(entree["action"], DECISION_CORRECTION)
        self.assertEqual(entree["instructions"], "un train moins cher")

    def test_route_refuser(self):
        client = self.conseiller()
        status, data = client.post(
            f"/api/propositions/{self.prop['id']}/refuser",
            {"motif": "budget insuffisant"})
        self.assertEqual(status, 200)
        self.assertEqual(data["proposition"]["statut"], STATUT_REFUSEE)
        self.assertEqual(data["proposition"]["decisions_statut"][-1]["action"],
                         DECISION_REFUSER)

    def test_route_sans_motif_pour_un_refus_renvoie_400(self):
        client = self.conseiller()
        status, data = client.post(f"/api/propositions/{self.prop['id']}/refuser", {})
        self.assertEqual(status, 400)
        self.assertEqual(data["erreur"]["code"], "validation_error")

    def test_route_sans_instructions_pour_une_correction_renvoie_400(self):
        client = self.conseiller()
        status, data = client.post(
            f"/api/propositions/{self.prop['id']}/correction", {"motif": "prix"})
        self.assertEqual(status, 400)
        self.assertEqual(data["erreur"]["code"], "validation_error")

    def test_route_accepter_sans_motif_renvoie_200(self):
        client = self.conseiller()
        status, data = client.post(f"/api/propositions/{self.prop['id']}/accepter", {})
        self.assertEqual(status, 200)
        self.assertEqual(data["proposition"]["statut"], STATUT_ENVOYEE)

    def test_route_proposition_inconnue_renvoie_404(self):
        client = self.conseiller()
        status, data = client.post("/api/propositions/prop_abc123/refuser",
                                   {"motif": "budget"})
        self.assertEqual(status, 404)
        self.assertEqual(data["erreur"]["code"], "proposition_not_found")

    def test_route_refusee_sans_session(self):
        client = ClientHTTP(self.base)
        status, data = client.post(f"/api/propositions/{self.prop['id']}/accepter",
                                   {"motif": "ok"})
        self.assertEqual(status, 401)
        self.assertEqual(data["erreur"]["code"], "auth_requise")

    def test_route_refusee_a_un_voyageur(self):
        client = self.voyageur()
        status, data = client.post(f"/api/propositions/{self.prop['id']}/accepter",
                                   {"motif": "ok"})
        self.assertEqual(status, 401)
        self.assertEqual(data["erreur"]["code"], "auth_requise")

    def test_une_action_refusee_ne_change_le_statut(self):
        client = self.voyageur()
        client.post(f"/api/propositions/{self.prop['id']}/accepter", {"motif": "ok"})
        self.assertEqual(self.props.obtenir(self.prop["id"])["statut"],
                         STATUT_BROUILLON)
        self.assertEqual(self.props.obtenir(self.prop["id"]).get("decisions_statut")
                         or [], [])

    def test_une_action_non_autorisee_par_l_etat_renvoie_400(self):
        client = self.conseiller()
        client.post(f"/api/propositions/{self.prop['id']}/refuser",
                    {"motif": "budget insuffisant"})
        status, data = client.post(f"/api/propositions/{self.prop['id']}/accepter",
                                   {"motif": "finalement ok"})
        self.assertEqual(status, 400)
        self.assertEqual(data["erreur"]["code"], "validation_error")
        self.assertEqual(self.props.obtenir(self.prop["id"])["statut"],
                         STATUT_REFUSEE)

    def test_la_decision_survit_au_rechargement(self):
        client = self.conseiller()
        client.post(f"/api/propositions/{self.prop['id']}/correction",
                    {"motif": "prix a revoir", "instructions": "un train moins cher"})
        status, data = client.get(f"/api/propositions/{self.prop['id']}")
        self.assertEqual(status, 200)
        self.assertEqual(data["proposition"]["statut"], STATUT_CORRECTION_DEMANDEE)
        self.assertEqual(len(data["proposition"]["decisions_statut"]), 1)


if __name__ == "__main__":
    unittest.main()
